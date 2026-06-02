import client from './client'

export const iniciarTrabajoPintura  = (item_id) =>
  client.post('/trabajos/pintura', { item_id }).then((r) => r.data)
export const cerrarTrabajoPintura   = (id, data) =>
  client.patch(`/trabajos/pintura/${id}/cerrar`, data).then((r) => r.data)
export const getMisTrabajosPintura  = () =>
  client.get('/trabajos/pintura/mis-trabajos').then((r) => r.data)

export const iniciarTrabajoRepuesto = (item_id) =>
  client.post('/trabajos/repuesto', { item_id }).then((r) => r.data)
export const cerrarTrabajoRepuesto  = (id, data) =>
  client.patch(`/trabajos/repuesto/${id}/cerrar`, data).then((r) => r.data)
export const getMisTrabajosRepuesto = () =>
  client.get('/trabajos/repuesto/mis-trabajos').then((r) => r.data)
