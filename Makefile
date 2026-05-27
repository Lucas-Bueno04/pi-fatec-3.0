.PHONY: help setup install install-backend \
        dev dev-web dev-mobile dev-desktop \
        deploy deploy-web deploy-mobile deploy-desktop \
        prod \
        test test-backend test-frontend \
        test-unit test-integration test-backend-cov test-frontend-cov \
        lint down logs seed

# ── Cores para output ────────────────────────────────────────────────────────
CYAN  := \033[0;36m
GREEN := \033[0;32m
YELLOW:= \033[0;33m
RESET := \033[0m

help:
	@echo ""
	@echo "$(CYAN)LabQuiz ETEC — Comandos disponíveis$(RESET)"
	@echo ""
	@echo "$(YELLOW)── 1ª vez (clone novo) ──────────────────────────────$(RESET)"
	@echo "  make setup              Configura tudo: venv + deps + infra + seed"
	@echo "  make install            Apenas instala dependências (sem infra/seed)"
	@echo "  make install-backend    Cria venv Python e instala deps do backend"
	@echo ""
	@echo "$(YELLOW)── Desenvolvimento (modo dev com hot-reload) ────────$(RESET)"
	@echo "  make dev-web            Infra + backend + frontend web  (:5173)"
	@echo "  make dev-mobile         Infra + backend + Expo Web (:8081, moldura de celular)"
	@echo "  make dev-desktop        Infra + backend + Electron"
	@echo ""
	@echo "$(YELLOW)── Deploy / Produção ─────────────────────────────────$(RESET)"
	@echo "  make deploy-web         Docker build + stack completa via Nginx (:80)"
	@echo "  make deploy-mobile      Gera bundle Expo de produção (dist/)"
	@echo "  make deploy-desktop     Gera instaladores Electron (AppImage/deb/exe)"
	@echo "  make deploy             Alias para deploy-web"
	@echo ""
	@echo "$(YELLOW)── Testes & Qualidade ────────────────────────────────$(RESET)"
	@echo "  make test               Roda TODOS os testes (backend + frontend)"
	@echo "  make test-unit          Apenas testes unitários do backend"
	@echo "  make test-integration   Apenas testes de integração do backend"
	@echo "  make test-backend       Pytest completo (unit + integration) com cobertura"
	@echo "  make test-backend-cov   Pytest com relatório HTML de cobertura"
	@echo "  make test-frontend      Jest + TypeScript check"
	@echo "  make test-frontend-cov  Jest com relatório de cobertura"
	@echo "  make lint               Flake8 (backend) + ESLint (frontend)"
	@echo ""
	@echo "$(YELLOW)── Infra ──────────────────────────────────────────────$(RESET)"
	@echo "  make down               Para todos os containers"
	@echo "  make logs               Exibe logs dos containers"
	@echo "  make seed               Popula banco com 60 questões + usuários demo"
	@echo ""

# ── Setup ────────────────────────────────────────────────────────────────────

## Inicialização completa — use na 1ª vez ou após clone
setup:
	@echo "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo "$(CYAN)  LabQuiz ETEC — Setup completo          $(RESET)"
	@echo "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo ""
	@echo "$(YELLOW)[1/5] Criando ambiente Python e instalando deps do backend...$(RESET)"
	@[ -d backend/venv ] || python3 -m venv backend/venv
	cd backend && ./venv/bin/pip install --quiet --upgrade pip
	cd backend && ./venv/bin/pip install --quiet -r requirements.txt
	@echo "$(GREEN)      ✓ Backend pronto$(RESET)"
	@echo ""
	@echo "$(YELLOW)[2/5] Instalando dependências do frontend web...$(RESET)"
	cd frontend && npm install --silent
	@echo "$(GREEN)      ✓ Frontend pronto$(RESET)"
	@echo ""
	@echo "$(YELLOW)[3/5] Criando arquivo .env do backend...$(RESET)"
	@[ -f backend/.env ] && echo "      .env já existe — mantido." || (cp backend/.env.example backend/.env && echo "$(GREEN)      ✓ .env criado de .env.example$(RESET)")
	@echo ""
	@echo "$(YELLOW)[4/5] Subindo MongoDB e Redis via Docker...$(RESET)"
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up mongodb redis -d
	@echo "$(CYAN)      Aguardando MongoDB ficar pronto...$(RESET)"
	@sleep 5
	@echo "$(GREEN)      ✓ Infra pronta$(RESET)"
	@echo ""
	@echo "$(YELLOW)[5/5] Populando banco com questões e usuários demo...$(RESET)"
	cd backend && ./venv/bin/python -c "from app.utils.seed import seed_db; import asyncio; asyncio.run(seed_db())"
	@echo ""
	@echo "$(GREEN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo "$(GREEN)  ✅ Setup concluído! Para iniciar o desenvolvimento:    $(RESET)"
	@echo "$(GREEN)                                                          $(RESET)"
	@echo "$(GREEN)     make dev-web       → Web (http://localhost:5173)    $(RESET)"
	@echo "$(GREEN)     make dev-mobile    → Mobile web (http://localhost:8081) $(RESET)"
	@echo "$(GREEN)     make dev-desktop   → Desktop (Electron)             $(RESET)"
	@echo "$(GREEN)                                                          $(RESET)"
	@echo "$(GREEN)  Credenciais de acesso:                                 $(RESET)"
	@echo "$(GREEN)     Admin   : admin@etec.sp.gov.br   / Admin@2025       $(RESET)"
	@echo "$(GREEN)     Prof    : professor@etec.sp.gov.br / Prof@2025      $(RESET)"
	@echo "$(GREEN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"

## Cria venv Python e instala deps do backend
install-backend:
	@echo "$(CYAN)▶ Criando venv Python...$(RESET)"
	@[ -d backend/venv ] || python3 -m venv backend/venv
	cd backend && ./venv/bin/pip install --quiet --upgrade pip
	cd backend && ./venv/bin/pip install --quiet -r requirements.txt
	@echo "$(GREEN)✅ Backend pronto$(RESET)"

install:
	@[ -d backend/venv ] || python3 -m venv backend/venv
	cd backend && ./venv/bin/pip install -r requirements.txt
	cd frontend && npm install
	cd mobile && npm install
	cd desktop && npm install

# ── Desenvolvimento ──────────────────────────────────────────────────────────

## Sobe infra + backend (background) + frontend web com hot-reload (:5173)
dev-web:
	@echo "$(CYAN)▶ Subindo MongoDB e Redis...$(RESET)"
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up mongodb redis -d
	@echo "$(CYAN)⏳ Aguardando infra ficar pronta...$(RESET)"
	@sleep 4
	@echo "$(CYAN)▶ Verificando .env do backend...$(RESET)"
	@[ -f backend/.env ] || cp backend/.env.example backend/.env
	@echo "$(CYAN)▶ Verificando dependências do backend...$(RESET)"
	@[ -f backend/venv/bin/uvicorn ] || (python3 -m venv backend/venv && cd backend && ./venv/bin/pip install -r requirements.txt)
	@echo "$(CYAN)▶ Verificando dependências do frontend...$(RESET)"
	@[ -d frontend/node_modules ] || (cd frontend && npm install)
	@echo "$(CYAN)▶ Populando banco (ignora se já populado)...$(RESET)"
	@cd backend && ./venv/bin/python -c "from app.utils.seed import seed_db; import asyncio; asyncio.run(seed_db())" 2>&1 | grep -E "✅|⚠|pulando|questões" || true
	@echo "$(CYAN)▶ Iniciando backend em background (porta 8000)...$(RESET)"
	@(cd backend && ./venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 2>&1 | sed 's/^/[backend] /') & \
	sleep 2 && \
	printf '\033[0;32m▶ Iniciando frontend web (porta 5173)...\033[0m\n' && \
	cd frontend && npm run dev

## Sobe infra + backend (background) + Expo Web — abre moldura de celular no navegador (:8081)
dev-mobile:
	@echo "$(CYAN)▶ Subindo MongoDB e Redis...$(RESET)"
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up mongodb redis -d
	@echo "$(CYAN)⏳ Aguardando infra ficar pronta...$(RESET)"
	@sleep 4
	@echo "$(CYAN)▶ Verificando .env do backend...$(RESET)"
	@[ -f backend/.env ] || cp backend/.env.example backend/.env
	@echo "$(CYAN)▶ Verificando dependências do backend...$(RESET)"
	@[ -f backend/venv/bin/uvicorn ] || (python3 -m venv backend/venv && cd backend && ./venv/bin/pip install -r requirements.txt)
	@echo "$(CYAN)▶ Verificando dependências do mobile...$(RESET)"
	@[ -d mobile/node_modules ] || (cd mobile && npm install)
	@echo "$(CYAN)▶ Populando banco (ignora se já populado)...$(RESET)"
	@cd backend && ./venv/bin/python -c "from app.utils.seed import seed_db; import asyncio; asyncio.run(seed_db())" 2>&1 | grep -E "✅|⚠|pulando|questões" || true
	@echo "$(CYAN)▶ Iniciando backend em background (porta 8000)...$(RESET)"
	@(cd backend && ./venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 2>&1 | sed 's/^/[backend] /') & \
	sleep 2 && \
	printf '\033[0;32m▶ Iniciando Expo Web em http://localhost:8081 (moldura de celular no navegador)...\033[0m\n' && \
	cd mobile && npx expo start --web --port 8081

## Sobe infra + backend (background) + Electron com hot-reload
dev-desktop:
	@echo "$(CYAN)▶ Subindo MongoDB e Redis...$(RESET)"
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up mongodb redis -d
	@echo "$(CYAN)⏳ Aguardando infra ficar pronta...$(RESET)"
	@sleep 4
	@echo "$(CYAN)▶ Verificando .env do backend...$(RESET)"
	@[ -f backend/.env ] || cp backend/.env.example backend/.env
	@echo "$(CYAN)▶ Verificando dependências do backend...$(RESET)"
	@[ -f backend/venv/bin/uvicorn ] || (python3 -m venv backend/venv && cd backend && ./venv/bin/pip install -r requirements.txt)
	@echo "$(CYAN)▶ Verificando dependências do desktop...$(RESET)"
	@[ -d desktop/node_modules ] || (cd desktop && npm install)
	@echo "$(CYAN)▶ Populando banco (ignora se já populado)...$(RESET)"
	@cd backend && ./venv/bin/python -c "from app.utils.seed import seed_db; import asyncio; asyncio.run(seed_db())" 2>&1 | grep -E "✅|⚠|pulando|questões" || true
	@echo "$(CYAN)▶ Iniciando backend em background (porta 8000)...$(RESET)"
	@(cd backend && ./venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 2>&1 | sed 's/^/[backend] /') & \
	sleep 2 && \
	printf '\033[0;32m▶ Iniciando Electron (aguarda Vite em :5173)...\033[0m\n' && \
	cd desktop && npm run dev

## Atalho legado — sobe apenas a infra e exibe instruções
dev:
	@echo "$(YELLOW)Dica: prefira 'make dev-web', 'make dev-mobile' ou 'make dev-desktop'$(RESET)"
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up mongodb redis -d
	@echo ""
	@echo "$(GREEN)MongoDB e Redis prontos. Inicie cada serviço manualmente:$(RESET)"
	@echo "  Backend : cd backend && ./venv/bin/uvicorn app.main:app --reload"
	@echo "  Web     : cd frontend && npm run dev"
	@echo "  Mobile  : cd mobile && npx expo start --web --port 8081"
	@echo "  Desktop : cd desktop && npm run dev"

# ── Deploy / Produção ────────────────────────────────────────────────────────

## Build Docker completo + sobe stack via Nginx na porta 80
deploy-web:
	@echo "$(CYAN)▶ Fazendo build e subindo stack completa via Docker...$(RESET)"
	docker compose up --build -d || \
		(echo "\n--- BACKEND LOGS ---" && docker compose logs backend && exit 1)
	@echo ""
	@echo "$(GREEN)✅ Web disponível em:   http://localhost$(RESET)"
	@echo "$(GREEN)📖 API Docs:            http://localhost/docs$(RESET)"

## Gera bundle de produção Expo (web export) em mobile/dist/
deploy-mobile:
	@echo "$(CYAN)▶ Gerando bundle Expo de produção...$(RESET)"
	cd mobile && npx expo export --platform all
	@echo ""
	@echo "$(GREEN)✅ Bundle gerado em mobile/dist/$(RESET)"
	@echo "$(YELLOW)   Para publicar: npx expo publish  ou  eas build$(RESET)"

## Build do frontend + gera instaladores Electron em desktop/dist/
deploy-desktop:
	@echo "$(CYAN)▶ Fazendo build do frontend...$(RESET)"
	cd frontend && npm run build
	@echo "$(CYAN)▶ Empacotando Electron...$(RESET)"
	cd desktop && npm run build
	@echo ""
	@echo "$(GREEN)✅ Instaladores gerados em desktop/dist/$(RESET)"
	@echo "   Linux  → desktop/dist/*.AppImage  /  *.deb"
	@echo "   Windows→ desktop/dist/*.exe"
	@echo "   macOS  → desktop/dist/*.dmg"

## Alias para deploy-web (stack Docker completa)
deploy: deploy-web

## Alias legado
prod: deploy-web

# ── Testes & Qualidade ───────────────────────────────────────────────────────

## Executa todos os testes (backend + frontend)
test: test-backend test-frontend

## Apenas testes unitários do backend (marcados com @pytest.mark.unit)
test-unit:
	@echo "$(CYAN)▶ Executando testes unitários do backend...$(RESET)"
	cd backend && ./venv/bin/pytest -m unit --cov=app --cov-report=term-missing -v
	@echo "$(GREEN)✅ Testes unitários concluídos$(RESET)"

## Apenas testes de integração do backend (marcados com @pytest.mark.integration)
test-integration:
	@echo "$(CYAN)▶ Executando testes de integração do backend...$(RESET)"
	cd backend && ./venv/bin/pytest -m integration --cov=app --cov-report=term-missing -v
	@echo "$(GREEN)✅ Testes de integração concluídos$(RESET)"

## Pytest completo (unit + integration) com cobertura mínima de 95%
test-backend:
	@echo "$(CYAN)▶ Executando todos os testes do backend (meta: ≥95% cobertura)...$(RESET)"
	cd backend && ./venv/bin/pytest --cov=app --cov-report=term-missing -v
	@echo "$(GREEN)✅ Testes do backend concluídos$(RESET)"

## Pytest com relatório HTML de cobertura (abre em htmlcov/index.html)
test-backend-cov:
	@echo "$(CYAN)▶ Gerando relatório HTML de cobertura do backend...$(RESET)"
	cd backend && ./venv/bin/pytest --cov=app --cov-report=term-missing --cov-report=html -v
	@echo ""
	@echo "$(GREEN)✅ Relatório gerado em backend/htmlcov/index.html$(RESET)"

## Jest + TypeScript check (sem watch)
test-frontend:
	@echo "$(CYAN)▶ Executando testes do frontend...$(RESET)"
	cd frontend && npm test -- --watchAll=false
	@echo "$(CYAN)▶ Verificando tipos TypeScript...$(RESET)"
	cd frontend && npx tsc --noEmit
	@echo "$(GREEN)✅ Testes do frontend concluídos$(RESET)"

## Jest com relatório de cobertura (coverage/lcov-report/index.html)
test-frontend-cov:
	@echo "$(CYAN)▶ Gerando relatório de cobertura do frontend...$(RESET)"
	cd frontend && npm test -- --watchAll=false --coverage
	@echo ""
	@echo "$(GREEN)✅ Relatório gerado em frontend/coverage/lcov-report/index.html$(RESET)"

lint:
	cd backend && python -m flake8 app tests --max-line-length=120 --ignore=E501
	cd frontend && npm run lint

# ── Infra ────────────────────────────────────────────────────────────────────

down:
	docker compose down

logs:
	docker compose logs -f --tail=100

seed:
	cd backend && ./venv/bin/python -c "from app.utils.seed import seed_db; import asyncio; asyncio.run(seed_db())"
