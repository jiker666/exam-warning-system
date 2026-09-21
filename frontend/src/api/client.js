import axios from 'axios'

// 统一 API 客户端：自动附加 JWT；登录失效自动跳转登录页
const client = axios.create({
  baseURL: '/api',
  timeout: 600000,
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

client.interceptors.response.use(
  (resp) => resp,
  (error) => {
    if (
      error.response?.status === 401 &&
      !window.location.pathname.startsWith('/login')
    ) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

/** 后端统一格式 {code, message, data}；失败抛出 Error(message) */
export async function request(config) {
  try {
    const resp = await client(config)
    return resp.data.data
  } catch (err) {
    const msg = err.response?.data?.message || err.message || '请求失败'
    throw new Error(msg)
  }
}

/** 通过带 JWT 的请求加载二进制资源（试卷图片 / 录像），返回 blob URL。
 *  后端返回的 url 可能自带 /api 前缀，而 client.baseURL 已是 /api，需先剥离避免 /api/api/ */
export async function fetchBlobUrl(url) {
  const path = url.startsWith('/api') ? url.slice(4) : url
  const resp = await client.get(path, { responseType: 'blob' })
  return URL.createObjectURL(resp.data)
}

export default client
