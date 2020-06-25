import { Notify } from "quasar";
import axios from "axios";

export function notifySuccessConfig(msg, timeout = 2000) {
  return {
    type: "positive",
    message: msg,
    timeout: timeout
  }
};

export function notifyErrorConfig(msg, timeout = 2000) {
  return {
    type: "negative",
    message: msg,
    timeout: timeout
  }
};

export function notifyWarningConfig(msg, timeout = 2000) {
  return {
    type: "warning",
    message: msg,
    timeout: timeout
  }
};

export function notifyInfoConfig(msg, timeout = 2000) {
  return {
    type: "info",
    message: msg,
    timeout: timeout
  }
};

export default {
  methods: {
    notifySuccess(msg, timeout = 2000) {
      Notify.create(notifySuccessConfig(msg, timeout));
    },
    notifyError(msg, timeout = 2000) {
      Notify.create(notifyErrorConfig(msg, timeout));
    },
    notifyWarning(msg, timeout = 2000) {
      Notify.create(notifyWarningConfig(msg, timeout));
    },
    notifyInfo(msg, timeout = 2000) {
      Notify.create(notifyInfoConfig(msg, timeout));
    },
    checkVer({ store }) {

      axios.get("/core/info/").then(r => {
        const version = r.data;

        if (localStorage.getItem("tacoffsitever")) {
          if (localStorage.getItem("tacoffsitever") === version) {
            return;
          } else {
            store.commit("SET_NEW_VER", true);
          }
        } else {
          localStorage.setItem("tacoffsitever", "0.0.1");
          return;
        }

      })
    }
  }
};
