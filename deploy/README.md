# Agendamento (não instalado automaticamente)
Semanal é suficiente: o SP156 publica por trimestre e o `update` só baixa o que mudou.

## systemd (usuário)
```bash
mkdir -p ~/.config/systemd/user
cp deploy/dados-publicos.{service,timer} ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now dados-publicos.timer
systemctl --user list-timers | grep dados
```
## ou cron
`0 3 * * 1 /caminho/do/projeto/deploy/run_update.sh`
