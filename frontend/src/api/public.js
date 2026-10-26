import request from './request'

export const getSite = () => request.get('/public/site/')
export const getCategories = (pageKey) =>
  request.get('/public/categories/', { params: { page_key: pageKey } })
export const listProjects = ({ pageKey, category, page_size = 12, offset = 0 }) =>
  request.get('/public/projects/', {
    params: { page_key: pageKey, category, page_size, offset },
  })
export const getProject = (slug) => request.get(`/public/projects/${slug}/`)
