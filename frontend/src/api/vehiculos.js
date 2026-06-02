import client from './client'

export const getVehiculos = (params) =>
  client.get('/vehiculos', { params }).then((r) => r.data)

export const getVehiculo = (vin) =>
  client.get(`/vehiculos/${vin}`).then((r) => r.data)
