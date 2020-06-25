import Vue from 'vue'
import VueRouter from 'vue-router'

import routes from './routes'

Vue.use(VueRouter)

export default function ({ store }) {
  const Router = new VueRouter({
    scrollBehavior: () => ({ x: 0, y: 0 }),
    routes,
    mode: process.env.VUE_ROUTER_MODE,
    base: process.env.VUE_ROUTER_BASE
  })

  Router.beforeEach((to, from, next) => {
    if (to.meta.requireAuth) {
      if (!store.getters.loggedIn) {
        next({
          name: "Login"
        });
      } else {
        next();
      }
    } else if (to.meta.requiresVisitor) {
      if (store.getters.loggedIn) {
        next({
          name: "Dashboard"
        });
      } else {
        next();
      }
    } else {
      next();
    }
  });


  return Router
}
