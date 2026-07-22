import React, { useState, useEffect } from 'react';
import auth from './msalConfig';
import api from './api';
import AppContext from './appContext';
import { useContext } from 'react';

function HeaderBar(props) {
    // provide a profile icon if user is not logged in
    const [menuOpen, setMenuOpen] = useState(false);
    const [isPinned, setIsPinned] = useState(false);
    const { searchText, setSearchText, selectedTab, allTasks, setAllTasks, refreshRequest } = useContext(AppContext);

    const toggleMenu = () => setMenuOpen(prev => !prev);

    const [profilePicture, setProfilePicture] = useState(null);

    const handleClose = () => {
        window.electronAPI.closeWindow(); // ✅ safe and works in browser context
    };

    useEffect(() => {
        const fetchProfilePicture = async () => {
            if (props.name) {
                const picture = await getProfilePicture(props.name);
                setProfilePicture(picture);
            }
        };
        fetchProfilePicture();
        handleRefresh();
    }, [props.name, refreshRequest]);

    const getProfilePicture = async (name) => {
        try {
            const response = await fetch(`https://graph.microsoft.com/v1.0/me/photo/$value`, {
                headers: {
                    Authorization: `Bearer ${props.token}`
                }
            });
            if (response.ok) {
                const blob = await response.blob();
                return URL.createObjectURL(blob);
            }
        } catch (error) {
            console.error("Error fetching profile picture:", error);
        }
        return null;
    };

    const handleLogout = () => {
        auth.msalInstance.logout();
    };

    const togglePin = () => setIsPinned(prev => !prev);
    const isLoggedIn = !!props.name;

    const handleSearch = (e) => {
        const query = e.target.value.toLowerCase();
        setSearchText(query);
    }

    const handleKeyDown = (e) => {
        if (e.key === 'Escape') {
            e.preventDefault();
            e.target.value = "";
            setSearchText("");
        }
    }

    const addnewtask = () => {
        const _searchText = searchText.trim();
        if (_searchText !== "") {
            api.addTask(_searchText, allTasks, selectedTab || "Tasks")
                .then(() => {
                    api.getTasks(true).then((data) => {
                        setAllTasks(data || []);
                        setSearchText("");
                    })
                });

        }
    }

    const handleRefresh = () => {
        api.getTasks(true).then((data) => {
            setAllTasks(data || []);
        })
    }

    return (
        <div className={`header-bar ${isPinned ? 'pinnedheader' : ''}`}>


            <div style={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                {/* grabber to drag the window and move to desired position     */}
                <div className="grabber" ><img src="images/grab.svg" className='img-icon'/></div>
                <div className='search-container'>
                    <img src="images/search.svg" className='img-icon'/>
                    <input type="text" placeholder="Search or add ..." className='search-box'
                        onChange={handleSearch} onKeyDown={handleKeyDown} value={searchText}
                    />
                    {searchText != "" && <button className='add-icon' onClick={addnewtask}><img src="images/add.svg" className='img-icon'/>&nbsp;&nbsp;Add New&nbsp;</button>}
                </div>
                <button className="menu-button" onClick={toggleMenu}>⋮</button>
            </div>
            <div className={`menu-container ${isPinned ? 'pinned' : ''}`}>

                {menuOpen && (
                    <div className="dropdown-menu">
                        {profilePicture ? (
                            <button>

                                <img className='icon profile-pic' src={profilePicture}
                                    alt="User profile" onClick={handleLogout} />
                                <span className='icon-text'>{props.name}   </span>
                            </button>
                        ) : (
                            <></>
                        )}
                        <button><img src="images/switch.svg" className='img-icon'/> <span className="icon-text">Switch User</span></button>
                        <button><img src="images/refresh.svg" className='img-icon'/><span className="icon-text" onClick={handleRefresh}>Refresh</span></button>
                        <button onClick={togglePin}>
                            {isPinned ? <><img src="images/unpin.svg" className='img-icon'/> <span className="icon-text">Unpin from Top</span></> : <><img src="images/pin.svg" className='img-icon'/> <span className="icon-text">Pin to Top</span></>}
                        </button>
                        {isLoggedIn && <button onClick={handleLogout}><img src="images/logout.svg" className='img-icon'/> <span className="icon-text">Logout</span></button>}
                        <div style={{ flex: 1 }}></div>
                        <button onClick={handleClose}>
                            <img src="images/close.svg" className='img-icon' style={{
                                backgroundColor: 'rgb(113 200 255)',
                                color: 'rgb(113 200 255)',
                                cursor: 'pointer'
                            }}/>
                            

                            <span className="icon-text"> Exit</span>
                        </button>

                    </div>
                )}
            </div>
        </div>
    );
};

export default HeaderBar;