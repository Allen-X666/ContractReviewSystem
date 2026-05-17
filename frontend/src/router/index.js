import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ROUTE_NAMES } from '@/utils/constants'

// 布局组件 - 懒加载
const DefaultLayout = () => import('@/layouts/DefaultLayout.vue')

// 预加载函数 - 用于空闲时预加载组件
function prefetchComponent(importFn) {
  if ('requestIdleCallback' in window) {
    requestIdleCallback(() => {
      importFn()
    }, { timeout: 2000 })
  } else {
    setTimeout(() => {
      importFn()
    }, 1000)
  }
}

// 页面组件
const routes = [
  {
    path: '/',
    component: DefaultLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: ROUTE_NAMES.DASHBOARD,
        component: () => import('@/views/dashboard/Index.vue'),
        meta: {
          title: '仪表盘',
          icon: 'DataLine',
          prefetch: true
        }
      },
      {
        path: 'contract',
        name: 'Contract',
        redirect: '/contract/list',
        meta: {
          title: '合同管理',
          icon: 'Document'
        },
        children: [
          {
            path: 'upload',
            name: ROUTE_NAMES.CONTRACT_UPLOAD,
            component: () => import('@/views/contract/Upload.vue'),
            meta: {
              title: '上传合同',
              icon: 'Upload',
              prefetch: true
            }
          },
          {
            path: 'list',
            name: ROUTE_NAMES.CONTRACT_LIST,
            component: () => import('@/views/contract/List.vue'),
            meta: {
              title: '合同列表',
              icon: 'List',
              prefetch: true
            }
          },
          {
            path: 'detail/:id',
            name: ROUTE_NAMES.CONTRACT_DETAIL,
            component: () => import('@/views/contract/Detail.vue'),
            meta: {
              title: '合同详情',
              hidden: true
            }
          }
        ]
      },
      {
        path: 'review/:contractId',
        name: ROUTE_NAMES.REVIEW,
        component: () => import('@/views/review/Index.vue'),
        meta: {
          title: '合同审查',
          hidden: true
        }
      },
      {
        path: 'report/:reviewId',
        name: ROUTE_NAMES.REPORT_PREVIEW,
        component: () => import('@/views/report/Preview.vue'),
        meta: {
          title: '审查报告',
          hidden: true
        }
      },
      {
        path: 'history',
        name: ROUTE_NAMES.HISTORY,
        component: () => import('@/views/history/Index.vue'),
        meta: {
          title: '审查历史',
          icon: 'Clock',
          prefetch: true
        }
      },
      {
        path: 'knowledge',
        name: ROUTE_NAMES.KNOWLEDGE,
        component: () => import('@/views/knowledge/Index.vue'),
        meta: {
          title: '法律知识库',
          icon: 'Collection'
        }
      },
      {
        path: 'template',
        name: ROUTE_NAMES.TEMPLATE,
        component: () => import('@/views/template/Index.vue'),
        meta: {
          title: '模板管理',
          icon: 'Files'
        }
      },
      {
        path: 'settings',
        name: ROUTE_NAMES.SETTINGS,
        component: () => import('@/views/settings/Index.vue'),
        meta: {
          title: '系统设置',
          icon: 'Setting',
          prefetch: true
        }
      },
      {
        path: 'admin',
        name: ROUTE_NAMES.ADMIN,
        component: () => import('@/views/admin/Index.vue'),
        meta: {
          title: '系统管理',
          icon: 'Setting',
          adminOnly: true
        }
      }
    ]
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: {
      title: '登录',
      public: true
    }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/Register.vue'),
    meta: {
      title: '注册',
      public: true
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/404.vue'),
    meta: {
      title: '页面不存在',
      public: true
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  // 设置页面标题
  document.title = to.meta.title 
    ? `${to.meta.title} - 智能合同审查助手` 
    : '智能合同审查助手'
  
  // 公开页面直接放行
  if (to.meta.public) {
    next()
    return
  }
  
  // 检查登录状态
  if (!userStore.isLoggedIn) {
    next('/login')
    return
  }

  // 检查admin权限（不区分大小写）
  if (to.meta.adminOnly && userStore.role?.toLowerCase() !== 'admin') {
    next('/dashboard')
    ElMessage.error('无权访问该页面')
    return
  }

  next()
})

// 路由后置守卫 - 用于预加载
router.afterEach((to) => {
  // 获取当前路由的所有兄弟路由和子路由
  const matched = to.matched
  if (!matched || matched.length === 0) return
  
  const lastMatched = matched[matched.length - 1]
  const parent = lastMatched?.parent
  
  if (parent) {
    // 预加载同级路由
    parent.children?.forEach(child => {
      if (child.meta?.prefetch && child.name !== to.name) {
        const component = child.components?.default
        if (typeof component === 'function') {
          prefetchComponent(component)
        }
      }
    })
  }
  
  // 预加载当前路由的子路由
  if (lastMatched?.children) {
    lastMatched.children.forEach(child => {
      if (child.meta?.prefetch) {
        const component = child.components?.default
        if (typeof component === 'function') {
          prefetchComponent(component)
        }
      }
    })
  }
})

export default router
