# Shepherd Runner

## INIT state

- [x] setup GPIO
- [x] setup runner MQTT
- [x] setup Hopper for client
- [x] load initial image
- [x] -> READY

## READY state

- [ ] robot reset (power)
- [ ] setup usercode
- [ ] start usercode
- [ ] wait for start command -> RUNNING

## RUNNING state

- [x] send start info
- [ ] wait for exit -> POST_RUN

## POST_RUN state

- [x] reset state
- [x] -> READY

