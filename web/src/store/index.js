import Vue from "vue";
import Vuex from "vuex";
import axios from "axios";
import { Notify } from "quasar";

Vue.use(Vuex);

export default function () {
  const Store = new Vuex.Store({
    modules: {
    },
    state: {
      username: localStorage.getItem("user_name") || null,
      token: localStorage.getItem("access_token") || null,
      newVer: false
    },
    getters: {
      loggedIn(state) {
        return state.token !== null;
      },
      userName(state) {
        return state.username;
      },
      needNewVer(state) {
        return state.newVer;
      }
    },
    mutations: {
      retrieveToken(state, { token, username }) {
        state.token = token;
        state.username = username;
      },
      destroyCommit(state) {
        state.token = null;
        state.username = null;
      },
      SET_NEW_VER_NEEDED(state, action) {
        state.newVer = action;
      }
    },
    actions: {
      checkVer(context) {
        axios.get("/core/version/").then(r => {
          const version = r.data;

          if (localStorage.getItem("tacoffsitever")) {
            if (localStorage.getItem("tacoffsitever") === version) {
              return;
            } else {
              localStorage.setItem("tacoffsitever", "0.0.1");
              context.commit("SET_NEW_VER_NEEDED", true);
            }
          } else {
            localStorage.setItem("tacoffsitever", version);
            return;
          }
        })
      },
      getNewVer() {
        localStorage.removeItem("tacoffsitever");
        location.reload();
      },
      retrieveToken(context, credentials) {
        return new Promise((resolve, reject) => {
          axios
            .post("/login/", credentials)
            .then(response => {
              const token = response.data.token;
              const username = credentials.username;
              localStorage.setItem("access_token", token);
              localStorage.setItem("user_name", username);
              context.commit("retrieveToken", { token, username });
              resolve(response);
            })
            .catch(error => {
              Notify.create({
                type: "negative",
                timeout: 1000,
                message: "Bad credentials"
              });
              reject(error);
            });
        });
      },
      destroyToken(context) {
        if (context.getters.loggedIn) {
          return new Promise((resolve, reject) => {
            axios
              .post("/logout/")
              .then(response => {
                localStorage.removeItem("access_token");
                localStorage.removeItem("user_name");
                context.commit("destroyCommit");
                resolve(response);
              })
              .catch(error => {
                localStorage.removeItem("access_token");
                localStorage.removeItem("user_name");
                context.commit("destroyCommit");
                reject(error);
              });
          });
        }
      }
    }
  });

  return Store;
}

