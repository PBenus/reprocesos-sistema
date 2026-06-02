import client from './client'

export const getReprocesos  = (params) => client.get('/reprocesos', { params }).then((r) => r.data)
export const getReproceso   = (id)     => client.get(`/reprocesos/${id}`).then((r) => r.data)
export const createReproceso = (data)  => client.post('/reprocesos', data).then((r) => r.data)
export const updateReproceso = (id, d) => client.patch(`/reprocesos/${id}`, d).then((r) => r.data)
export const deleteReproceso = (id)    => client.delete(`/reprocesos/${id}`).then((r) => r.data)

export const addItemPintura  = (reprocesoId, data) =>
  client.post(`/reprocesos/${reprocesoId}/items/pintura`, data).then((r) => r.data)
export const addItemRepuesto = (reprocesoId, data) =>
  client.post(`/reprocesos/${reprocesoId}/items/repuesto`, data).then((r) => r.data)
export const deleteItemPintura  = (reprocesoId, itemId) =>
  client.delete(`/reprocesos/${reprocesoId}/items/pintura/${itemId}`).then((r) => r.data)
export const deleteItemRepuesto = (reprocesoId, itemId) =>
  client.delete(`/reprocesos/${reprocesoId}/items/repuesto/${itemId}`).then((r) => r.data)
