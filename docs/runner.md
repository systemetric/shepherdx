# Shepherd Runner

## INIT state

- [ ] setup GPIO
- [x] setup runner MQTT
- [ ] setup Hopper for client
- [x] load initial image
- [x] -> READY

## READY state

- [ ] robot reset (power)
- [ ] setup usercode
- [ ] start usercode
- [ ] wait for start command -> RUNNING

## RUNNING state

- [ ] send start info
- [ ] wait for exit -> POST_RUN

## POST_RUN state

- [x] reset state
- [x] -> READY

