import auth from './msalConfig';

const api = {
    addTask: async function (title, allTasks, listName = "Tasks") {
        let that = this;

        // add tasks to the MSTODO list
        const list = allTasks.find(list => list.listName === listName);
        if (!list) {
            return;
        }
        return fetch(`https://graph.microsoft.com/v1.0/me/todo/lists/${list.id}/tasks`, {
            method: 'POST',
            headers: {
                Authorization: `Bearer ${that.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: title,
                status: "notStarted"
            })
        });
    },
    runAuthFlow: async function () {
        await auth.msalInstance.initialize();
        const loginResponse = await auth.msalInstance.handleRedirectPromise();
        if (loginResponse) {

            const tokenResponse = await auth.msalInstance.acquireTokenSilent({
                ...auth.loginRequest,
                account: loginResponse.account,
                scopes: ['User.Read']
            });
            this.token = tokenResponse.accessToken;
            return { account: loginResponse.account, token: tokenResponse.accessToken };
        }
    },
    requestLogin: () => auth.msalInstance.loginRedirect(auth.requestConfig),
    getTasks: async function (refresh = false) {

        const token = this.token;
        let that = this

        return fetch("https://graph.microsoft.com/v1.0/me/todo/lists", {
            headers: { Authorization: `Bearer ${token}` }
        }).then(res => res.json())
            .then(async data => {
                const lists = data.value;
                // Fetch tasks for each list in parallel
                const taskPromises = (lists || []).map(list => {
                    return fetch(`https://graph.microsoft.com/v1.0/me/todo/lists/${list.id}/tasks`, {
                        headers: { Authorization: `Bearer ${token}` }
                    })
                        .then(res => res.json())
                        .then(taskData => ({
                            id: list.id,
                            listName: list.displayName,
                            tasks: taskData.value || []
                        }))
                });

                return await Promise.all(taskPromises);

            });
    },


    toggleStatus: async function (taskId, allTasks, currentStatus) {
        const token = this.token;
        let that = this;
        // Find the task and its parent list
        for (let list of allTasks) {
            if (!list || !list.tasks) continue;
            const task = list.tasks.find(t => t.id === taskId);
            if (task) {
                // Update the task status to completed
                return fetch(`https://graph.microsoft.com/v1.0/me/todo/lists/${list.id}/tasks/${taskId}`, {
                    method: 'PATCH',
                    headers: {
                        Authorization: `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        status: currentStatus === 'completed' ? 'notStarted' : 'completed'
                    })
                });
            }
        }
        return Promise.reject("Task not found");
    },
    setDueDate: async function (taskId, dueDate, allTasks) {
        const token = this.token;
        let that = this;
        // Find the task and its parent list
        for (let list of allTasks) {
            if (!list || !list.tasks) continue;
            const task = list.tasks.find(t => t.id === taskId);
            if (task) {
                // Update the task due date
                return fetch(`https://graph.microsoft.com/v1.0/me/todo/lists/${list.id}/tasks/${taskId}`, {
                    method: 'PATCH',
                    headers: {
                        Authorization: `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        dueDateTime: {
                            dateTime: dueDate,
                            timeZone: "UTC"
                        }
                    })
                });
            }
        }
        return Promise.reject("Task not found");
    }
}

export default api;