const routes = [
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {
        path: '', name:
          'Dashboard',
        component: () => import('pages/Dashboard.vue'),
        meta: {
          requireAuth: true
        }
      },
      {
        path: '/Agents',
        name: 'Agents',
        component: () => import('pages/Agents.vue'),
        meta: {
          requireAuth: true
        }
      },
      {
        path: '/OffsiteJobs',
        name: 'OffsiteJobs',
        component: () => import('pages/OffsiteJobs.vue'),
        meta: {
          requireAuth: true
        }
      },
      {
        path: '/BackupJobs',
        name: 'BackupJobs',
        component: () => import('pages/BackupJobs.vue'),
        meta: {
          requireAuth: true
        }
      }
    ]
  },
  {
    path: '/Login',
    name: 'Login',
    component: () => import('pages/Login.vue'),
    meta: {
      requiresVisitor: true
    }
  },
  {
    path: '/Expired',
    name: 'Expired',
    component: () => import('pages/SessionExpired.vue')
  }
]

// Always leave this as last one
routes.push({
  path: '*',
  name: "404",
  component: () => import('pages/Error404.vue')
})

export default routes
