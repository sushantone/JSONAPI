import { PublicClientApplication } from "@azure/msal-browser";

const cliendId = process.env.REACT_APP_CLIENT_ID;
const appId = process.env.REACT_APP_PROTOCOL_ID; // Ensure this matches your .env file
// src/msalConfig.js
const msalConfig = {
  auth: {
    clientId: cliendId,
    authority: "https://login.microsoftonline.com/common",
    redirectUri:  
    //`${appId}://auth` 
     "http://localhost:3000" 
    // window.location.href
  },
  system: {
    navigateToLoginRequestUrl: false
  }
};

const requestConfig = {
  scopes: ["User.Read", "Tasks.ReadWrite"]
};

export default {msalInstance  : new PublicClientApplication(msalConfig), requestConfig};