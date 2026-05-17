import request from '@/utils/request'

/**
 * 获取系统信息
 * @returns {Promise}
 */
export function getSystemInfo() {
  return request({
    url: '/system/info',
    method: 'get'
  })
}
