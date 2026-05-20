import { createRouter, createWebHistory, defineAsyncComponent } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ROUTE_NAMES } from '@/utils/constants'
import { ElLoading } from 'element-plus'

// 布局组件 - 懒加载
const DefaultLayout = () => import('@/layouts/DefaultLayout.vue')

// 骨架屏组件（轻量级，直接导入）
import PageSkeleton from '@/components/Skeleton/PageSkeleton.vue'

// 异步组件加载器 - 带骨架屏 Loading
function createAsyncComponent(importFn, options = {}) {
  const { delay = 200, timeout = 10000, skeletonProps = {} } = options
  
  return defineAsyncComponent({
    loader: importFn,
    loadingComponent: PageSkeleton,
    delay,
    timeout,
    errorComponent: {
      template: `
        <div class="async-error">
          <el-result
            icon="error"
            title="加载失败"
            sub-title="页面加载失败，请刷新重试"
          >
            <template #extra>
              <el-button type="primary" @click="$router.go(0)">刷新页面</el-button>
            </template>
          </el-result>
        </div>
      `
    },
    onError(error, retry, fail, attempts) {
      if (attempts <= 3) {
        retry()
      } else {
        fail()
      }
    }
  })
}

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

// 页面组件 - 使用 defineAsyncComponent + 骨架屏
const DashboardView = createAsyncComponent(() => import('@/views/dashboard/Index.vue'))
const ContractUploadView = createAsyncComponent(() => import('@/views/contract/Upload.vue'))
const ContractListView = createAsyncComponent(() => import('@/views/contract/List.vue'))
const ContractDetailView = createAsyncComponent(() => import('@/views/contract/Detail.vue'))
const ReviewView = createAsyncComponent(() => import('@/views/review/Index.vue'))
const ReportPreviewView = createAsyncComponent(() => import('@/views/report/Preview.vue'))
const HistoryView = createAsyncComponent(() => import('@/views/history/Index.vue'))
const KnowledgeView = createAsyncComponent(() => import('@/views/knowledge/Index.vue'))
const TemplateView = createAsyncComponent(() => import('@/views/template/Index.vue'))
const SettingsView = createAsyncComponent(() => import('@/views/settings/Index.vue'))
const AdminView = createAsyncComponent(() => import('@/views/admin/Index.vue'))
const LoginView = createAsyncComponent(() => import('@/views/auth/Login.vue'))
const RegisterView = createAsyncComponent(() => import('@/views/auth/Register.vue'))
const NotFoundView = createAsyncComponent(() => import('@/views/error/404.vue'))

const routes = [
  {
    path: '/',
    component: DefaultLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: ROUTE_NAMES.DASHBOARD,
        component: DashboardView,
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
            component: ContractUploadView,
            meta: {
              title: '上传合同',
              icon: 'Upload',
              prefetch: true
            }
          },
          {
            path: 'list',
            name: ROUTE_NAMES.CONTRACT_LIST,
            component: ContractListView,
            meta: {
              title: '合同列表',
              icon: 'List',
              prefetch: true
            }
          },
          {
            path: 'detail/:id',
            name: ROUTE_NAMES.CONTRACT_DETAIL,
            component: ContractDetailView,
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
        component: ReviewView,
        meta: {
          title: '合同审查',
          hidden: true
        }
      },
      {
        path: 'report/:reviewId',
        name: ROUTE_NAMES.REPORT_PREVIEW,
        component: ReportPreviewView,
        meta: {
          title: '审查报告',
          hidden: true
        }
      },
      {
        path: 'history',
        name: ROUTE_NAMES.HISTORY,
        component: HistoryView,
        meta: {
          title: '审查历史',
          icon: 'Clock',
          prefetch: true
        }
      },
      {
        path: 'knowledge',
        name: ROUTE_NAMES.KNOWLEDGE,
        component: KnowledgeView,
        meta: {
          title: '法律知识库',
          icon: 'Collection'
        }
      },
      {
        path: 'template',
        name: ROUTE_NAMES.TEMPLATE,
        component: TemplateView,
        meta: {
          title: '模板管理',
          icon: 'Files'
        }
      },
      {
        path: 'settings',
        name: ROUTE_NAMES.SETTINGS,
        component: SettingsView,
        meta: {
          title: '系统设置',
          icon: 'Setting',
          prefetch: true
        }
      },
      {
        path: 'admin',
        name: ROUTE_NAMES.ADMIN,
        component: AdminView,
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
    component: LoginView,
    meta: {
      title: '登录',
      public: true
    }
  },
  {
    path: '/register',
    name: 'Register',
    component: RegisterView,
    meta: {
      title: '注册',
      public: true
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFoundView,
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
