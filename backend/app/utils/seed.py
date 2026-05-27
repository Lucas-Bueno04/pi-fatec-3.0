"""
=============================================================================
LABQUIZ ETEC — Seed: 60 questões de laboratório de Química
=============================================================================
Distribuição:
  24 × FACIL   — identificação básica de vidrarias e materiais
  21 × MEDIO   — função de materiais e procedimentos simples
  15 × DIFICIL — sistemas experimentais, associações e conceitos avançados

Uso:
  cd backend
  ./venv/bin/python -c "from app.utils.seed import seed_db; import asyncio; asyncio.run(seed_db())"
  # ou:
  make seed
=============================================================================
"""
import asyncio
from datetime import datetime
from typing import List

from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger

from ..core.config import settings
from ..models.question import Question, Alternative, AssociationPair, QuestionType, DifficultyLevel
from ..models.user import User, UserRole, LGPDConsent, UserProgress
from ..security.password import hash_password


# ── Seed data ─────────────────────────────────────────────────────────────────

QUESTIONS: List[dict] = [

    # ══════════════════════════════════════════════════════════════════════
    #  FÁCIL — Identificação básica de vidrarias e materiais (20 questões)
    # ══════════════════════════════════════════════════════════════════════

    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "FACIL",
        "text": "Qual vidraria é usada para medir volumes de líquidos com alta precisão?",
        "alternatives": [
            {"id": "a1", "text": "Proveta", "is_correct": True,
             "alt_text": "Proveta graduada cilíndrica"},
            {"id": "a2", "text": "Béquer", "is_correct": False, "alt_text": "Béquer de vidro"},
            {"id": "a3", "text": "Funil", "is_correct": False, "alt_text": "Funil de vidro"},
            {"id": "a4", "text": "Cadinho", "is_correct": False, "alt_text": "Cadinho de porcelana"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "A proveta possui escala graduada precisa para medição de volumes.",
        "material_name": "Proveta",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "FACIL",
        "text": "Qual material de laboratório é utilizado para aquecer substâncias diretamente na chama?",
        "alternatives": [
            {"id": "a1", "text": "Béquer", "is_correct": True,
             "alt_text": "Béquer cilíndrico de vidro borossilicato"},
            {"id": "a2", "text": "Balão volumétrico", "is_correct": False, "alt_text": "Balão volumétrico"},
            {"id": "a3", "text": "Erlenmyer", "is_correct": False, "alt_text": "Frasco Erlenmyer"},
            {"id": "a4", "text": "Dessecador", "is_correct": False, "alt_text": "Dessecador"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "O béquer de vidro borossilicato resiste a variações de temperatura e é adequado para aquecimento.",
        "material_name": "Béquer",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "FACIL",
        "text": "Qual é o instrumento de medição de temperatura mais comum no laboratório de química?",
        "alternatives": [
            {"id": "a1", "text": "Termômetro", "is_correct": True, "alt_text": "Termômetro de mercúrio"},
            {"id": "a2", "text": "Manômetro", "is_correct": False, "alt_text": "Manômetro"},
            {"id": "a3", "text": "Barômetro", "is_correct": False, "alt_text": "Barômetro"},
            {"id": "a4", "text": "Densímetro", "is_correct": False, "alt_text": "Densímetro"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "O termômetro mede temperatura. No laboratório são comuns termômetros de mercúrio ou digitais.",
        "material_name": "Termômetro",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "FACIL",
        "text": "Qual vidraria possui formato cônico e é usada principalmente em titulações?",
        "alternatives": [
            {"id": "a1", "text": "Erlenmyer", "is_correct": True, "alt_text": "Frasco Erlenmyer cônico"},
            {"id": "a2", "text": "Proveta", "is_correct": False, "alt_text": "Proveta"},
            {"id": "a3", "text": "Balão de fundo redondo", "is_correct": False, "alt_text": "Balão de fundo redondo"},
            {"id": "a4", "text": "Tubo de ensaio", "is_correct": False, "alt_text": "Tubo de ensaio"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "O Erlenmyer tem base cônica que facilita a agitação sem respingos, ideal para titulações.",
        "material_name": "Erlenmyer",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "FACIL",
        "text": "Qual instrumento é usado para pesar amostras com precisão no laboratório?",
        "alternatives": [
            {"id": "a1", "text": "Balança analítica", "is_correct": True, "alt_text": "Balança analítica digital"},
            {"id": "a2", "text": "Densímetro", "is_correct": False, "alt_text": "Densímetro"},
            {"id": "a3", "text": "Proveta", "is_correct": False, "alt_text": "Proveta graduada"},
            {"id": "a4", "text": "Pipeta", "is_correct": False, "alt_text": "Pipeta volumétrica"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "A balança analítica mede massas com precisão de 0,0001 g.",
        "material_name": "Balança analítica",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "FACIL",
        "text": "Qual vidraria possui um único traço de calibração e é usada para transferir volume exato?",
        "alternatives": [
            {"id": "a1", "text": "Pipeta volumétrica", "is_correct": True, "alt_text": "Pipeta volumétrica de 1 traço"},
            {"id": "a2", "text": "Pipeta graduada", "is_correct": False, "alt_text": "Pipeta graduada"},
            {"id": "a3", "text": "Bureta", "is_correct": False, "alt_text": "Bureta"},
            {"id": "a4", "text": "Seringa", "is_correct": False, "alt_text": "Seringa"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "A pipeta volumétrica tem uma marca única de calibração para transferência de volume exato.",
        "material_name": "Pipeta volumétrica",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "FACIL",
        "text": "Qual material é utilizado para filtrar sólidos de soluções?",
        "alternatives": [
            {"id": "a1", "text": "Papel de filtro", "is_correct": True, "alt_text": "Papel de filtro circular"},
            {"id": "a2", "text": "Papel de pH", "is_correct": False, "alt_text": "Papel indicador de pH"},
            {"id": "a3", "text": "Papel absorvente", "is_correct": False, "alt_text": "Papel absorvente"},
            {"id": "a4", "text": "Membrana de diálise", "is_correct": False, "alt_text": "Membrana de diálise"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "O papel de filtro possui poros que retêm sólidos e permitem a passagem do líquido.",
        "material_name": "Papel de filtro",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "FACIL",
        "text": "Qual equipamento é utilizado para aplicar calor uniforme a substâncias no laboratório?",
        "alternatives": [
            {"id": "a1", "text": "Bico de Bunsen", "is_correct": True, "alt_text": "Bico de Bunsen com chama azul"},
            {"id": "a2", "text": "Estufa", "is_correct": False, "alt_text": "Estufa de secagem"},
            {"id": "a3", "text": "Manta elétrica", "is_correct": False, "alt_text": "Manta aquecedora elétrica"},
            {"id": "a4", "text": "Banho-maria", "is_correct": False, "alt_text": "Banho-maria"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "O bico de Bunsen produz chama controlada de gás para aquecimento direto.",
        "material_name": "Bico de Bunsen",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "FACIL",
        "text": "O que é um bastão de vidro usado para fazer no laboratório?",
        "alternatives": [
            {"id": "a1", "text": "Agitar soluções e auxiliar na decantação", "is_correct": True,
             "alt_text": "Bastão de vidro sendo usado para agitar"},
            {"id": "a2", "text": "Medir temperatura", "is_correct": False, "alt_text": "Termômetro"},
            {"id": "a3", "text": "Filtrar soluções", "is_correct": False, "alt_text": "Funil com papel filtro"},
            {"id": "a4", "text": "Medir volumes", "is_correct": False, "alt_text": "Proveta"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "O bastão de vidro é usado para agitar soluções, guiar líquidos durante a decantação e misturar substâncias.",
        "material_name": "Bastão de vidro",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "FACIL",
        "text": "Qual vidraria é usada para armazenar e servir reagentes líquidos?",
        "alternatives": [
            {"id": "a1", "text": "Frasco reagente", "is_correct": True, "alt_text": "Frasco reagente com tampa"},
            {"id": "a2", "text": "Béquer", "is_correct": False, "alt_text": "Béquer"},
            {"id": "a3", "text": "Proveta", "is_correct": False, "alt_text": "Proveta"},
            {"id": "a4", "text": "Bureta", "is_correct": False, "alt_text": "Bureta"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "Os frascos reagentes são projetados para armazenar substâncias com segurança, com tampas herméticas.",
        "material_name": "Frasco reagente",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "FACIL",
        "text": "Qual material de proteção individual é obrigatório no laboratório de química?",
        "alternatives": [
            {"id": "a1", "text": "Óculos de proteção", "is_correct": True, "alt_text": "Óculos de proteção laboratorial"},
            {"id": "a2", "text": "Chapéu de segurança", "is_correct": False, "alt_text": "Chapéu de segurança"},
            {"id": "a3", "text": "Protetor solar", "is_correct": False, "alt_text": "Protetor solar"},
            {"id": "a4", "text": "Cinto de segurança", "is_correct": False, "alt_text": "Cinto de segurança"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "Os óculos de proteção protegem os olhos de respingos de reagentes e fragmentos de vidro.",
        "material_name": "EPI - Óculos de proteção",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "FACIL",
        "text": "Qual vidraria é especialmente projetada para reações com gás, com saída lateral?",
        "alternatives": [
            {"id": "a1", "text": "Tubo de ensaio com saída lateral (tubo de kipp)", "is_correct": True,
             "alt_text": "Frasco com saída lateral para coleta de gás"},
            {"id": "a2", "text": "Erlenmyer simples", "is_correct": False, "alt_text": "Erlenmyer"},
            {"id": "a3", "text": "Balão de fundo redondo", "is_correct": False, "alt_text": "Balão de fundo redondo"},
            {"id": "a4", "text": "Béquer", "is_correct": False, "alt_text": "Béquer"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "O frasco gerador de gás possui saída lateral (tubo) para coletar ou redirecionar gases produzidos.",
        "material_name": "Frasco gerador de gás",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "FACIL",
        "text": "Qual instrumento é utilizado para verificar o pH de uma solução?",
        "alternatives": [
            {"id": "a1", "text": "pHmetro", "is_correct": True, "alt_text": "pHmetro digital com eletrodo"},
            {"id": "a2", "text": "Condutivímetro", "is_correct": False, "alt_text": "Condutivímetro"},
            {"id": "a3", "text": "Espectrofotômetro", "is_correct": False, "alt_text": "Espectrofotômetro"},
            {"id": "a4", "text": "Cromatógrafo", "is_correct": False, "alt_text": "Cromatógrafo"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "O pHmetro mede eletronicamente a concentração de íons H⁺, determinando o pH com precisão.",
        "material_name": "pHmetro",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "FACIL",
        "text": "Qual vidraria tem fundo plano e é ideal para aquecimento em chapa elétrica?",
        "alternatives": [
            {"id": "a1", "text": "Béquer", "is_correct": True, "alt_text": "Béquer de fundo plano"},
            {"id": "a2", "text": "Balão de fundo redondo", "is_correct": False, "alt_text": "Balão de fundo redondo"},
            {"id": "a3", "text": "Frasco de Erlenmeyer", "is_correct": False, "alt_text": "Erlenmyer"},
            {"id": "a4", "text": "Kitassato", "is_correct": False, "alt_text": "Kitassato"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "O béquer com fundo plano tem maior área de contato com a chapa aquecedora, garantindo aquecimento uniforme.",
        "material_name": "Béquer",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "FACIL",
        "text": "Qual é a função principal do funil de separação (funil de decantação)?",
        "alternatives": [
            {"id": "a1", "text": "Separar dois líquidos imiscíveis", "is_correct": True,
             "alt_text": "Funil de separação com duas fases líquidas"},
            {"id": "a2", "text": "Filtrar soluções sólidas", "is_correct": False,
             "alt_text": "Filtragem de sólidos"},
            {"id": "a3", "text": "Medir volumes precisos", "is_correct": False,
             "alt_text": "Medição de volume"},
            {"id": "a4", "text": "Armazenar ácidos concentrados", "is_correct": False,
             "alt_text": "Armazenamento de ácidos"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "O funil de separação é usado para separar líquidos de densidades diferentes que não se misturam.",
        "material_name": "Funil de separação",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "FACIL",
        "text": "Qual equipamento de proteção coletiva deve estar presente na bancada de laboratório?",
        "alternatives": [
            {"id": "a1", "text": "Chuveiro de emergência e lava-olhos", "is_correct": True,
             "alt_text": "Chuveiro de emergência e lava-olhos"},
            {"id": "a2", "text": "Ar-condicionado", "is_correct": False, "alt_text": "Ar-condicionado"},
            {"id": "a3", "text": "Geladeira", "is_correct": False, "alt_text": "Geladeira"},
            {"id": "a4", "text": "Televisão", "is_correct": False, "alt_text": "Televisão"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "Chuveiro de emergência e lava-olhos são EPCs obrigatórios para acidentes com químicos.",
        "material_name": "EPC - Chuveiro e lava-olhos",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "FACIL",
        "text": "O que é um espátula de laboratório usada para fazer?",
        "alternatives": [
            {"id": "a1", "text": "Transferir sólidos e pós", "is_correct": True,
             "alt_text": "Espátula metálica de laboratório"},
            {"id": "a2", "text": "Agitar líquidos", "is_correct": False, "alt_text": "Bastão de vidro"},
            {"id": "a3", "text": "Medir volumes", "is_correct": False, "alt_text": "Proveta"},
            {"id": "a4", "text": "Filtrar soluções", "is_correct": False, "alt_text": "Papel de filtro"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "A espátula metálica é usada para transferir, recolher ou manipular sólidos e pós.",
        "material_name": "Espátula",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "FACIL",
        "text": "Qual vidraria possui gargalo longo e é usada para destilar líquidos?",
        "alternatives": [
            {"id": "a1", "text": "Balão de destilação", "is_correct": True,
             "alt_text": "Balão de destilação com saída lateral"},
            {"id": "a2", "text": "Balão volumétrico", "is_correct": False, "alt_text": "Balão volumétrico"},
            {"id": "a3", "text": "Kitassato", "is_correct": False, "alt_text": "Kitassato"},
            {"id": "a4", "text": "Béquer", "is_correct": False, "alt_text": "Béquer"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "O balão de destilação possui saída lateral (colo) para permitir a saída dos vapores durante a destilação.",
        "material_name": "Balão de destilação",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "FACIL",
        "text": "Qual material é usado para suportar o funil durante a filtração?",
        "alternatives": [
            {"id": "a1", "text": "Suporte universal com argola", "is_correct": True,
             "alt_text": "Suporte universal com argola metálica"},
            {"id": "a2", "text": "Tripé de ferro", "is_correct": False, "alt_text": "Tripé"},
            {"id": "a3", "text": "Garra metálica", "is_correct": False, "alt_text": "Garra"},
            {"id": "a4", "text": "Estante para tubos", "is_correct": False, "alt_text": "Estante"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "O suporte universal com argola segura o funil na altura correta durante a filtração.",
        "material_name": "Suporte universal",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "FACIL",
        "text": "Qual é a vidraria usada exclusivamente para preparar soluções de concentração exata?",
        "alternatives": [
            {"id": "a1", "text": "Balão volumétrico", "is_correct": True,
             "alt_text": "Balão volumétrico com traço de calibração"},
            {"id": "a2", "text": "Béquer", "is_correct": False, "alt_text": "Béquer"},
            {"id": "a3", "text": "Proveta", "is_correct": False, "alt_text": "Proveta"},
            {"id": "a4", "text": "Erlenmyer", "is_correct": False, "alt_text": "Erlenmyer"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "O balão volumétrico possui um único traço de calibração que garante volume exato para preparação de soluções.",
        "material_name": "Balão volumétrico",
    },

    # ══════════════════════════════════════════════════════════════════════
    #  MÉDIO — Função de materiais e procedimentos (18 questões)
    # ══════════════════════════════════════════════════════════════════════

    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "MEDIO",
        "text": "Durante uma titulação, qual vidraria é usada para liberar o titulante gota a gota?",
        "alternatives": [
            {"id": "a1", "text": "Bureta", "is_correct": True, "alt_text": "Bureta de 50 mL"},
            {"id": "a2", "text": "Pipeta volumétrica", "is_correct": False, "alt_text": "Pipeta volumétrica"},
            {"id": "a3", "text": "Proveta", "is_correct": False, "alt_text": "Proveta"},
            {"id": "a4", "text": "Erlenmyer", "is_correct": False, "alt_text": "Erlenmyer"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "A bureta é graduada e possui torneira que permite adicionar o titulante gota a gota com controle preciso.",
        "material_name": "Bureta",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "MEDIO",
        "text": "Por que o balão volumétrico NÃO deve ser aquecido diretamente?",
        "alternatives": [
            {"id": "a1", "text": "O aquecimento dilata o vidro e altera o volume calibrado",
             "is_correct": True, "alt_text": "Balão volumétrico com marca de calibração"},
            {"id": "a2", "text": "Porque o vidro pode mudar de cor", "is_correct": False,
             "alt_text": "Mudança de cor no vidro"},
            {"id": "a3", "text": "Porque ele não suporta calor", "is_correct": False,
             "alt_text": "Vidro quebrando"},
            {"id": "a4", "text": "Porque o gargalo é muito curto", "is_correct": False,
             "alt_text": "Gargalo curto"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "O calor causa dilatação do vidro, alterando o volume interno e comprometendo a precisão da solução.",
        "material_name": "Balão volumétrico",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "MEDIO",
        "text": "Qual é a função do condensador (refrigerante) no sistema de destilação?",
        "alternatives": [
            {"id": "a1", "text": "Resfriar e condensar os vapores em líquido",
             "is_correct": True, "alt_text": "Condensador de Liebig com água circulante"},
            {"id": "a2", "text": "Aquecer o líquido para vaporização", "is_correct": False,
             "alt_text": "Aquecimento do líquido"},
            {"id": "a3", "text": "Filtrar impurezas do destilado", "is_correct": False,
             "alt_text": "Filtração do destilado"},
            {"id": "a4", "text": "Medir a temperatura de ebulição", "is_correct": False,
             "alt_text": "Medição de temperatura"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "O condensador (refrigerante de Liebig) resfria os vapores através de água circulante, condensando-os.",
        "material_name": "Condensador",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "MEDIO",
        "text": "Para que serve o dessecador no laboratório de química?",
        "alternatives": [
            {"id": "a1", "text": "Manter amostras em ambiente seco, sem umidade",
             "is_correct": True, "alt_text": "Dessecador com sílica gel"},
            {"id": "a2", "text": "Aquecer amostras uniformemente", "is_correct": False,
             "alt_text": "Aquecimento uniforme"},
            {"id": "a3", "text": "Evaporar soluções", "is_correct": False, "alt_text": "Evaporação"},
            {"id": "a4", "text": "Filtrar gases", "is_correct": False, "alt_text": "Filtração de gases"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "O dessecador contém agente dessecante (sílica gel) que absorve umidade, preservando amostras sensíveis.",
        "material_name": "Dessecador",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "MEDIO",
        "text": "Qual é a diferença entre uma pipeta volumétrica e uma pipeta graduada?",
        "alternatives": [
            {"id": "a1", "text": "A volumétrica tem 1 traço (volume fixo); a graduada tem vários (volumes variáveis)",
             "is_correct": True, "alt_text": "Pipeta volumétrica com 1 traço vs graduada com múltiplos"},
            {"id": "a2", "text": "A volumétrica é maior; a graduada é menor",
             "is_correct": False, "alt_text": "Diferença de tamanho"},
            {"id": "a3", "text": "São iguais, apenas nomes diferentes", "is_correct": False,
             "alt_text": "Pipetas iguais"},
            {"id": "a4", "text": "A graduada é mais precisa que a volumétrica", "is_correct": False,
             "alt_text": "Comparação de precisão"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "Pipeta volumétrica: 1 traço, volume fixo e alta precisão. Pipeta graduada: vários traços, volume variável.",
        "material_name": "Pipetas",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "MEDIO",
        "text": "Qual procedimento deve ser feito antes de usar o bico de Bunsen?",
        "alternatives": [
            {"id": "a1", "text": "Verificar conexões de gás e regular a entrada de ar",
             "is_correct": True, "alt_text": "Verificação do bico de Bunsen"},
            {"id": "a2", "text": "Mergulhá-lo em água por 5 minutos", "is_correct": False,
             "alt_text": "Mergulho em água"},
            {"id": "a3", "text": "Aquecê-lo na estufa por 10 minutos", "is_correct": False,
             "alt_text": "Aquecimento na estufa"},
            {"id": "a4", "text": "Calibrá-lo com solução salina", "is_correct": False,
             "alt_text": "Calibração com solução"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "Antes do uso: verificar vazamentos nas conexões de gás e ajustar a entrada de ar para chama azul segura.",
        "material_name": "Bico de Bunsen",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "MEDIO",
        "text": "Qual equipamento é usado para centrifugar amostras e separar componentes por densidade?",
        "alternatives": [
            {"id": "a1", "text": "Centrífuga", "is_correct": True, "alt_text": "Centrífuga laboratorial"},
            {"id": "a2", "text": "Agitador magnético", "is_correct": False, "alt_text": "Agitador magnético"},
            {"id": "a3", "text": "Rotavapor", "is_correct": False, "alt_text": "Rotavapor"},
            {"id": "a4", "text": "Sonicador", "is_correct": False, "alt_text": "Sonicador de ultrassom"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "A centrífuga usa força centrífuga para separar componentes de densidades diferentes em amostras.",
        "material_name": "Centrífuga",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "MEDIO",
        "text": "Por que a câmara de exaustão (capela) é usada ao trabalhar com substâncias voláteis?",
        "alternatives": [
            {"id": "a1", "text": "Para aspirar vapores tóxicos e proteger o operador",
             "is_correct": True, "alt_text": "Capela de exaustão com vidro frontal"},
            {"id": "a2", "text": "Para aumentar a temperatura dos reagentes", "is_correct": False,
             "alt_text": "Aquecimento de reagentes"},
            {"id": "a3", "text": "Para refrigerar amostras sensíveis", "is_correct": False,
             "alt_text": "Refrigeração de amostras"},
            {"id": "a4", "text": "Para filtrar partículas sólidas", "is_correct": False,
             "alt_text": "Filtração de sólidos"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "A capela aspira vapores perigosos, protegendo o operador de inalação de substâncias tóxicas ou corrosivas.",
        "material_name": "Capela de exaustão",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "MEDIO",
        "text": "Qual é a função do tubo de Soxhlet na extração de substâncias?",
        "alternatives": [
            {"id": "a1", "text": "Extrair continuamente compostos de sólidos usando solvente quente",
             "is_correct": True, "alt_text": "Extrator Soxhlet com solvente"},
            {"id": "a2", "text": "Separar líquidos por diferença de densidade", "is_correct": False,
             "alt_text": "Separação por densidade"},
            {"id": "a3", "text": "Medir absorção de luz em soluções", "is_correct": False,
             "alt_text": "Absorção de luz"},
            {"id": "a4", "text": "Centrifugar amostras líquidas", "is_correct": False,
             "alt_text": "Centrifugação"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "O extrator Soxhlet recicla solvente continuamente para extrair compostos de amostras sólidas.",
        "material_name": "Extrator Soxhlet",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "MEDIO",
        "text": "Qual a função do indicador ácido-base durante uma titulação?",
        "alternatives": [
            {"id": "a1", "text": "Indicar o ponto de equivalência por mudança de cor",
             "is_correct": True, "alt_text": "Erlenmyer com indicador de cor mudando"},
            {"id": "a2", "text": "Acelerar a reação de neutralização", "is_correct": False,
             "alt_text": "Catálise da reação"},
            {"id": "a3", "text": "Aumentar a concentração do titulante", "is_correct": False,
             "alt_text": "Concentração aumentada"},
            {"id": "a4", "text": "Diminuir o volume de titulante necessário", "is_correct": False,
             "alt_text": "Menor volume"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "O indicador muda de cor no ponto de equivalência (ou próximo), sinalizando o fim da titulação.",
        "material_name": "Indicador ácido-base",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "MEDIO",
        "text": "Qual equipamento mede a absorbância de soluções para determinar concentrações?",
        "alternatives": [
            {"id": "a1", "text": "Espectrofotômetro", "is_correct": True,
             "alt_text": "Espectrofotômetro UV-Vis"},
            {"id": "a2", "text": "Cromatógrafo", "is_correct": False, "alt_text": "Cromatógrafo"},
            {"id": "a3", "text": "Potenciômetro", "is_correct": False, "alt_text": "Potenciômetro"},
            {"id": "a4", "text": "Condutivímetro", "is_correct": False, "alt_text": "Condutivímetro"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "O espectrofotômetro mede a absorbância da luz por soluções, permitindo calcular concentrações pela Lei de Beer.",
        "material_name": "Espectrofotômetro",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "MEDIO",
        "text": "Qual procedimento correto para diluir um ácido concentrado em água?",
        "alternatives": [
            {"id": "a1", "text": "Adicionar o ácido lentamente sobre a água, nunca o contrário",
             "is_correct": True, "alt_text": "Ácido sendo adicionado à água"},
            {"id": "a2", "text": "Adicionar água sobre o ácido concentrado", "is_correct": False,
             "alt_text": "Água sobre ácido — PERIGO"},
            {"id": "a3", "text": "Misturar simultaneamente em partes iguais", "is_correct": False,
             "alt_text": "Mistura simultânea"},
            {"id": "a4", "text": "Não importa a ordem", "is_correct": False,
             "alt_text": "Qualquer ordem"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "Sempre adicionar ácido à água (AAA). A reação é exotérmica; adicionar água ao ácido pode causar explosão.",
        "material_name": "Segurança - Diluição de ácidos",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "MEDIO",
        "text": "Qual é a função do cadinho de porcelana no laboratório?",
        "alternatives": [
            {"id": "a1", "text": "Incinerar amostras em altas temperaturas (calcinação)",
             "is_correct": True, "alt_text": "Cadinho de porcelana com tampa"},
            {"id": "a2", "text": "Medir volumes pequenos de líquido", "is_correct": False,
             "alt_text": "Medição de volume"},
            {"id": "a3", "text": "Armazenar ácidos concentrados", "is_correct": False,
             "alt_text": "Armazenamento de ácidos"},
            {"id": "a4", "text": "Preparar soluções tampão", "is_correct": False,
             "alt_text": "Soluções tampão"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "O cadinho de porcelana suporta temperaturas acima de 1000°C e é usado na calcinação (queima) de amostras.",
        "material_name": "Cadinho de porcelana",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "MEDIO",
        "text": "Para que é utilizada a estufa de secagem no laboratório?",
        "alternatives": [
            {"id": "a1", "text": "Remover umidade de amostras e vidrarias a temperatura controlada",
             "is_correct": True, "alt_text": "Estufa de secagem com controle de temperatura"},
            {"id": "a2", "text": "Esterilizar materiais com radiação UV", "is_correct": False,
             "alt_text": "Esterilização UV"},
            {"id": "a3", "text": "Congelar amostras biológicas", "is_correct": False,
             "alt_text": "Congelamento"},
            {"id": "a4", "text": "Produzir vapores para reações", "is_correct": False,
             "alt_text": "Produção de vapores"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "A estufa remove umidade de vidrarias e amostras, garantindo resultados gravimétricos precisos.",
        "material_name": "Estufa de secagem",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "MEDIO",
        "text": "Qual é a função do agitador magnético no laboratório?",
        "alternatives": [
            {"id": "a1", "text": "Agitar soluções continuamente usando barra magnética giratória",
             "is_correct": True, "alt_text": "Agitador magnético com barra giratória"},
            {"id": "a2", "text": "Misturar pós sólidos em alta rotação", "is_correct": False,
             "alt_text": "Mistura de pós"},
            {"id": "a3", "text": "Separar compostos por campo magnético", "is_correct": False,
             "alt_text": "Separação magnética"},
            {"id": "a4", "text": "Medir a viscosidade de soluções", "is_correct": False,
             "alt_text": "Medição de viscosidade"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "O agitador magnético gera campo magnético rotativo que faz a barra de agitação girar, homogeneizando soluções.",
        "material_name": "Agitador magnético",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "MEDIO",
        "text": "O kitassato é uma vidraria especial. Qual é sua função principal?",
        "alternatives": [
            {"id": "a1", "text": "Coleta do filtrado durante filtração a vácuo",
             "is_correct": True, "alt_text": "Kitassato conectado à trompa d'água"},
            {"id": "a2", "text": "Armazenar soluções em baixa pressão", "is_correct": False,
             "alt_text": "Armazenamento em baixa pressão"},
            {"id": "a3", "text": "Titular ácidos com bases", "is_correct": False,
             "alt_text": "Titulação"},
            {"id": "a4", "text": "Medir volumes de gases", "is_correct": False,
             "alt_text": "Medição de gases"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "O kitassato tem saída lateral conectada à trompa d'água, permitindo filtração a vácuo (filtração rápida).",
        "material_name": "Kitassato",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "MEDIO",
        "text": "Qual é a diferença entre filtração simples e filtração a vácuo?",
        "alternatives": [
            {"id": "a1", "text": "Filtração a vácuo é mais rápida e usa kitassato + trompa d'água",
             "is_correct": True, "alt_text": "Comparação dos dois tipos de filtração"},
            {"id": "a2", "text": "A filtração simples usa pressão; a vácuo usa gravidade",
             "is_correct": False, "alt_text": "Inversão das forças"},
            {"id": "a3", "text": "São idênticas, apenas com equipamentos diferentes",
             "is_correct": False, "alt_text": "Processos idênticos"},
            {"id": "a4", "text": "Filtração a vácuo separa apenas sólidos grandes",
             "is_correct": False, "alt_text": "Sólidos grandes"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "Filtração simples usa gravidade; filtração a vácuo aplica pressão reduzida, acelerando o processo.",
        "material_name": "Filtração a vácuo",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "MEDIO",
        "text": "Qual equipamento é usado para medir a condutividade elétrica de uma solução?",
        "alternatives": [
            {"id": "a1", "text": "Condutivímetro", "is_correct": True, "alt_text": "Condutivímetro com eletrodo"},
            {"id": "a2", "text": "pHmetro", "is_correct": False, "alt_text": "pHmetro"},
            {"id": "a3", "text": "Espectrofotômetro", "is_correct": False, "alt_text": "Espectrofotômetro"},
            {"id": "a4", "text": "Polarímetro", "is_correct": False, "alt_text": "Polarímetro"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "O condutivímetro mede a capacidade da solução de conduzir corrente elétrica, indicando presença de íons.",
        "material_name": "Condutivímetro",
    },

    # ══════════════════════════════════════════════════════════════════════
    #  DIFÍCIL — Sistemas experimentais e conceitos avançados (12 questões)
    # ══════════════════════════════════════════════════════════════════════

    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "DIFICIL",
        "text": "Em um sistema de destilação fracionada, qual é a função da coluna de fracionamento (coluna de Vigreux)?",
        "alternatives": [
            {"id": "a1", "text": "Aumentar as trocas de calor entre vapor e líquido, separando compostos por ponto de ebulição próximo",
             "is_correct": True, "alt_text": "Coluna de Vigreux com entalhes internos"},
            {"id": "a2", "text": "Condensar completamente todos os vapores antes de sair",
             "is_correct": False, "alt_text": "Condensação total"},
            {"id": "a3", "text": "Aquecer o líquido antes de entrar no balão",
             "is_correct": False, "alt_text": "Pré-aquecimento"},
            {"id": "a4", "text": "Filtrar impurezas sólidas do destilado",
             "is_correct": False, "alt_text": "Filtração de sólidos"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "A coluna de Vigreux cria equilíbrio líquido-vapor repetido, permitindo separar compostos com pontos de ebulição próximos.",
        "system_name": "Destilação fracionada",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "DIFICIL",
        "text": "Na cromatografia em coluna, o que determina a ordem de eluição dos compostos?",
        "alternatives": [
            {"id": "a1", "text": "A afinidade de cada composto pela fase estacionária relativa à fase móvel",
             "is_correct": True, "alt_text": "Coluna cromatográfica com bandas coloridas"},
            {"id": "a2", "text": "O tamanho molecular dos compostos",
             "is_correct": False, "alt_text": "Tamanho molecular"},
            {"id": "a3", "text": "A temperatura da fase móvel",
             "is_correct": False, "alt_text": "Temperatura"},
            {"id": "a4", "text": "A densidade dos compostos",
             "is_correct": False, "alt_text": "Densidade"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "Compostos com maior afinidade pela fase estacionária são retidos mais tempo; com menor afinidade, eluem primeiro.",
        "system_name": "Cromatografia em coluna",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "DIFICIL",
        "text": "No sistema de extração líquido-líquido, qual propriedade determina em qual fase um composto se concentra?",
        "alternatives": [
            {"id": "a1", "text": "O coeficiente de distribuição (K) do composto entre os dois solventes",
             "is_correct": True, "alt_text": "Funil de separação com duas fases e extração"},
            {"id": "a2", "text": "O ponto de ebulição do composto",
             "is_correct": False, "alt_text": "Ponto de ebulição"},
            {"id": "a3", "text": "A viscosidade dos solventes",
             "is_correct": False, "alt_text": "Viscosidade"},
            {"id": "a4", "text": "A pressão atmosférica local",
             "is_correct": False, "alt_text": "Pressão atmosférica"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "O coeficiente de distribuição K = [soluto na fase orgânica] / [soluto na fase aquosa] determina a partição.",
        "system_name": "Extração líquido-líquido",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "DIFICIL",
        "text": "Em titulação potenciométrica, por que se usa pHmetro em vez de indicador visual?",
        "alternatives": [
            {"id": "a1", "text": "Para detectar o ponto de equivalência com precisão em soluções coloridas ou opacas",
             "is_correct": True, "alt_text": "Montagem de titulação potenciométrica"},
            {"id": "a2", "text": "Porque indicadores visuais são mais caros",
             "is_correct": False, "alt_text": "Custo do indicador"},
            {"id": "a3", "text": "Porque o pHmetro acelera a reação de neutralização",
             "is_correct": False, "alt_text": "Aceleração da reação"},
            {"id": "a4", "text": "Porque indicadores só funcionam em bases",
             "is_correct": False, "alt_text": "Indicadores apenas em bases"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "A titulação potenciométrica usa o pHmetro para monitorar o pH continuamente, determinando o ponto de equivalência com precisão.",
        "system_name": "Titulação potenciométrica",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "DIFICIL",
        "text": "No sistema de refluxo, qual é o objetivo de condensar e retornar o solvente ao balão?",
        "alternatives": [
            {"id": "a1", "text": "Manter a concentração da mistura constante durante o aquecimento prolongado",
             "is_correct": True, "alt_text": "Sistema de refluxo com condensador e balão"},
            {"id": "a2", "text": "Aumentar a pressão interna do sistema",
             "is_correct": False, "alt_text": "Aumento de pressão"},
            {"id": "a3", "text": "Separar os componentes por ponto de ebulição",
             "is_correct": False, "alt_text": "Separação por ebulição"},
            {"id": "a4", "text": "Filtrar resíduos sólidos formados durante a reação",
             "is_correct": False, "alt_text": "Filtração de resíduos"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "No refluxo, o condensador retorna o vapor condensado ao balão, mantendo volumes e concentrações constantes durante aquecimento longo.",
        "system_name": "Sistema de refluxo",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "DIFICIL",
        "text": "Em espectroscopia de absorção atômica (AAS), qual é a função do atomizador?",
        "alternatives": [
            {"id": "a1", "text": "Converter a amostra líquida em átomos livres no estado gasoso",
             "is_correct": True, "alt_text": "Atomizador de chama do espectrofotômetro de absorção atômica"},
            {"id": "a2", "text": "Ionizar os átomos para análise de massa",
             "is_correct": False, "alt_text": "Ionização de átomos"},
            {"id": "a3", "text": "Separar os isótopos do elemento analisado",
             "is_correct": False, "alt_text": "Separação isotópica"},
            {"id": "a4", "text": "Amplificar o sinal de absorção por ressonância",
             "is_correct": False, "alt_text": "Amplificação por ressonância"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "O atomizador (chama ou forno de grafite) volatiliza e dissocia os compostos, gerando átomos livres que absorvem a radiação.",
        "system_name": "Espectroscopia de absorção atômica",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "DIFICIL",
        "text": "Qual é a vantagem do método de adição de padrão em análise quantitativa por espectrofotometria?",
        "alternatives": [
            {"id": "a1", "text": "Minimizar erros de matriz, pois o padrão é adicionado diretamente na amostra real",
             "is_correct": True, "alt_text": "Curva de adição de padrão em espectrofotometria"},
            {"id": "a2", "text": "Reduzir o tempo de análise pela metade",
             "is_correct": False, "alt_text": "Redução do tempo"},
            {"id": "a3", "text": "Eliminar a necessidade de calibração",
             "is_correct": False, "alt_text": "Sem calibração"},
            {"id": "a4", "text": "Aumentar a sensibilidade do detector",
             "is_correct": False, "alt_text": "Aumento de sensibilidade"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "O método de adição de padrão corrige efeitos de matriz (interferências), pois o padrão é adicionado à própria amostra.",
        "system_name": "Espectrofotometria - adição de padrão",
    },
    {
        "type": "ASSOCIACAO_FUNCAO", "difficulty": "DIFICIL",
        "text": "Associe cada vidraria à sua função principal no laboratório de química analítica.",
        "alternatives": [],
        "association_pairs": [
            {"material_id": "m1", "material_name": "Bureta",
             "target_id": "t1", "target_text": "Liberar titulante gota a gota com volume controlado"},
            {"material_id": "m2", "material_name": "Balão volumétrico",
             "target_id": "t2", "target_text": "Preparar soluções de concentração exata"},
            {"material_id": "m3", "material_name": "Pipeta volumétrica",
             "target_id": "t3", "target_text": "Transferir volume exato e fixo de líquido"},
            {"material_id": "m4", "material_name": "Erlenmyer",
             "target_id": "t4", "target_text": "Receber o titulado durante a titulação"},
        ],
        "explanation": "Bureta → titulante; Balão volumétrico → solução padrão; Pipeta volumétrica → alíquota exata; Erlenmyer → titulado.",
        "system_name": "Vidrarias analíticas",
    },
    {
        "type": "ASSOCIACAO_SISTEMA", "difficulty": "DIFICIL",
        "text": "Associe cada sistema de separação ao seu princípio de funcionamento.",
        "alternatives": [],
        "association_pairs": [
            {"material_id": "s1", "material_name": "Destilação simples",
             "target_id": "p1", "target_text": "Separação de líquidos com pontos de ebulição muito diferentes"},
            {"material_id": "s2", "material_name": "Destilação fracionada",
             "target_id": "p2", "target_text": "Separação de líquidos com pontos de ebulição próximos"},
            {"material_id": "s3", "material_name": "Extração líquido-líquido",
             "target_id": "p3", "target_text": "Separação baseada na solubilidade em dois solventes imiscíveis"},
            {"material_id": "s4", "material_name": "Cromatografia",
             "target_id": "p4", "target_text": "Separação baseada na afinidade por fase estacionária e móvel"},
        ],
        "explanation": "Cada técnica de separação baseia-se em propriedades físico-químicas distintas dos compostos.",
        "system_name": "Técnicas de separação",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "DIFICIL",
        "text": "No método gravimétrico de precipitação, qual erro sistemático pode ocorrer se o precipitado não for lavado adequadamente?",
        "alternatives": [
            {"id": "a1", "text": "Co-precipitação: íons contaminantes ficam retidos no precipitado",
             "is_correct": True, "alt_text": "Precipitado com contaminantes"},
            {"id": "a2", "text": "O precipitado se dissolve completamente na solução",
             "is_correct": False, "alt_text": "Dissolução do precipitado"},
            {"id": "a3", "text": "A balança analítica não consegue pesar o material",
             "is_correct": False, "alt_text": "Problema na balança"},
            {"id": "a4", "text": "O filtro de papel se degrada durante a calcinação",
             "is_correct": False, "alt_text": "Degradação do filtro"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "A co-precipitação contamina o precipitado com outros íons da solução, levando a resultados com massa maior que o esperado.",
        "system_name": "Gravimetria de precipitação",
    },
    {
        "type": "ASSOCIACAO_FUNCAO", "difficulty": "DIFICIL",
        "text": "Associe cada equipamento de segurança à sua função de proteção no laboratório.",
        "alternatives": [],
        "association_pairs": [
            {"material_id": "e1", "material_name": "Óculos de proteção",
             "target_id": "f1", "target_text": "Proteger os olhos de respingos e fragmentos"},
            {"material_id": "e2", "material_name": "Jaleco de algodão",
             "target_id": "f2", "target_text": "Proteger a pele e roupa de respingos de reagentes"},
            {"material_id": "e3", "material_name": "Luvas de nitrila",
             "target_id": "f3", "target_text": "Proteger as mãos de substâncias corrosivas e tóxicas"},
            {"material_id": "e4", "material_name": "Máscara respiratória",
             "target_id": "f4", "target_text": "Proteger as vias respiratórias de vapores e aerossóis"},
        ],
        "explanation": "Cada EPI protege uma parte do corpo: óculos (olhos), jaleco (corpo), luvas (mãos), máscara (sistema respiratório).",
        "system_name": "Equipamentos de proteção individual",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "DIFICIL",
        "text": "Na análise por HPLC (Cromatografia Líquida de Alta Eficiência), o que é o tempo de retenção (tR)?",
        "alternatives": [
            {"id": "a1", "text": "O tempo que o analito leva para percorrer a coluna e chegar ao detector",
             "is_correct": True, "alt_text": "Cromatograma HPLC com pico e tempo de retenção"},
            {"id": "a2", "text": "O tempo de vida útil da coluna cromatográfica",
             "is_correct": False, "alt_text": "Vida útil da coluna"},
            {"id": "a3", "text": "O tempo de equilíbrio da fase estacionária",
             "is_correct": False, "alt_text": "Equilíbrio da fase estacionária"},
            {"id": "a4", "text": "O tempo máximo para injetar a amostra no sistema",
             "is_correct": False, "alt_text": "Tempo de injeção"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "O tempo de retenção é característico de cada composto e permite sua identificação em condições cromatográficas definidas.",
        "system_name": "HPLC - Cromatografia líquida",
    },

    # ══════════════════════════════════════════════════════════════════════
    #  QUESTÕES EXTRAS (10) — Materiais, indicadores e técnicas avançadas
    #  Algumas são projetadas para uso com imagens (marcadas com image_alt_text)
    # ══════════════════════════════════════════════════════════════════════

    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "FACIL",
        "text": "O gral e pistilo é utilizado no laboratório principalmente para:",
        "image_alt_text": "Gral de porcelana branco com pistilo",
        "alternatives": [
            {"id": "a1", "text": "Triturar e pulverizar sólidos", "is_correct": True,
             "alt_text": "Gral e pistilo triturando sólido"},
            {"id": "a2", "text": "Medir volumes de líquidos", "is_correct": False,
             "alt_text": "Proveta"},
            {"id": "a3", "text": "Aquecer substâncias diretamente na chama", "is_correct": False,
             "alt_text": "Béquer sobre chama"},
            {"id": "a4", "text": "Filtrar soluções com partículas finas", "is_correct": False,
             "alt_text": "Papel de filtro em funil"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "O gral (recipiente) e pistilo (bastão) são usados para triturar, moer e pulverizar sólidos antes de análises.",
        "material_name": "Gral e pistilo",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "FACIL",
        "text": "Para que é utilizado o vidro de relógio no laboratório?",
        "image_alt_text": "Vidro de relógio circular côncavo de borossilicato",
        "alternatives": [
            {"id": "a1", "text": "Evaporar pequenas amostras e servir de tampa para béqueres",
             "is_correct": True, "alt_text": "Vidro de relógio com amostra"},
            {"id": "a2", "text": "Medir temperatura de soluções", "is_correct": False,
             "alt_text": "Termômetro"},
            {"id": "a3", "text": "Medir volumes precisos de líquidos", "is_correct": False,
             "alt_text": "Proveta"},
            {"id": "a4", "text": "Filtrar precipitados de soluções", "is_correct": False,
             "alt_text": "Funil com papel de filtro"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "O vidro de relógio é usado como suporte para evaporação, pesagem de sólidos e como tampa para béqueres.",
        "material_name": "Vidro de relógio",
    },
    {
        "type": "ASSOCIACAO_FUNCAO", "difficulty": "FACIL",
        "text": "Associe cada material de suporte laboratorial à sua função principal.",
        "alternatives": [],
        "association_pairs": [
            {"material_id": "m1", "material_name": "Tripé de ferro",
             "target_id": "t1", "target_text": "Suportar equipamentos sobre a chama do bico de Bunsen"},
            {"material_id": "m2", "material_name": "Tela de amianto",
             "target_id": "t2", "target_text": "Distribuir uniformemente o calor da chama no fundo do béquer"},
            {"material_id": "m3", "material_name": "Pinça de madeira",
             "target_id": "t3", "target_text": "Segurar tubos de ensaio aquecidos sem risco de queimadura"},
            {"material_id": "m4", "material_name": "Vidro de relógio",
             "target_id": "t4", "target_text": "Evaporar pequenas quantidades de líquido e pesar sólidos"},
        ],
        "explanation": "Tripé (suporte) + Tela de amianto (distribuição de calor) + Pinça de madeira (segurança) + Vidro de relógio (evaporação/pesagem).",
        "material_name": "Materiais de suporte",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "FACIL",
        "text": "Qual é a função da trompa d'água no laboratório de química?",
        "alternatives": [
            {"id": "a1", "text": "Gerar vácuo para filtração a vácuo e dessecadores",
             "is_correct": True, "alt_text": "Trompa d'água conectada à torneira e ao kitassato"},
            {"id": "a2", "text": "Aquecer água para banho-maria", "is_correct": False,
             "alt_text": "Banho-maria aquecendo"},
            {"id": "a3", "text": "Medir a vazão de água no laboratório", "is_correct": False,
             "alt_text": "Medidor de vazão"},
            {"id": "a4", "text": "Filtrar impurezas da água destilada", "is_correct": False,
             "alt_text": "Filtro de água"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "A trompa d'água (Venturi) usa o fluxo de água para criar vácuo parcial, essencial na filtração a vácuo com kitassato.",
        "material_name": "Trompa d'água",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "MEDIO",
        "text": "Qual é a função principal do rotavapor (evaporador rotativo) no laboratório?",
        "alternatives": [
            {"id": "a1", "text": "Evaporar solventes sob vácuo a baixa temperatura, preservando compostos termossensíveis",
             "is_correct": True, "alt_text": "Rotavapor com balão giratório e condensador"},
            {"id": "a2", "text": "Agitar amostras em alta rotação para homogeneização", "is_correct": False,
             "alt_text": "Agitador de alta rotação"},
            {"id": "a3", "text": "Centrifugar precipitados em alta velocidade", "is_correct": False,
             "alt_text": "Centrífuga"},
            {"id": "a4", "text": "Destilar completamente líquidos aquosos à pressão atmosférica", "is_correct": False,
             "alt_text": "Destilação simples"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "O rotavapor combina rotação (aumenta superfície de evaporação), vácuo (abaixa ponto de ebulição) e condensador para recuperar solvente.",
        "material_name": "Rotavapor",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "MEDIO",
        "text": "Para que é utilizado o forno de mufla (mufla) no laboratório?",
        "alternatives": [
            {"id": "a1", "text": "Calcinação de amostras em altas temperaturas (acima de 500 °C)",
             "is_correct": True, "alt_text": "Forno de mufla com câmara interna refratária"},
            {"id": "a2", "text": "Secagem rápida de vidrarias a 105 °C", "is_correct": False,
             "alt_text": "Estufa de secagem"},
            {"id": "a3", "text": "Esterilização de meios de cultura por calor úmido", "is_correct": False,
             "alt_text": "Autoclave"},
            {"id": "a4", "text": "Fusão de amostras metálicas para espectrometria", "is_correct": False,
             "alt_text": "Cadinho metálico"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "A mufla atinge temperaturas entre 500 °C e 1200 °C para calcinação (destruição de matéria orgânica) em análises gravimétricas.",
        "material_name": "Forno de mufla",
    },
    {
        "type": "ASSOCIACAO_FUNCAO", "difficulty": "MEDIO",
        "text": "Associe cada indicador ácido-base à sua faixa de viragem (mudança de cor).",
        "alternatives": [],
        "association_pairs": [
            {"material_id": "i1", "material_name": "Fenolftaleína",
             "target_id": "v1", "target_text": "Incolor (pH < 8,2) → Rosa intenso (pH > 10,0)"},
            {"material_id": "i2", "material_name": "Tornassol",
             "target_id": "v2", "target_text": "Vermelho em meio ácido → Azul em meio básico"},
            {"material_id": "i3", "material_name": "Alaranjado de metila",
             "target_id": "v3", "target_text": "Vermelho (pH < 3,1) → Amarelo (pH > 4,4)"},
            {"material_id": "i4", "material_name": "Verde de bromo-cresol",
             "target_id": "v4", "target_text": "Amarelo (pH < 3,8) → Azul (pH > 5,4)"},
        ],
        "explanation": "Cada indicador possui uma faixa de pH de viragem específica, escolhida conforme o ponto de equivalência da titulação.",
        "material_name": "Indicadores ácido-base",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "DIFICIL",
        "text": "No cromatógrafo gasoso (CG), qual é a função do detector de ionização de chama (FID)?",
        "alternatives": [
            {"id": "a1",
             "text": "Detectar compostos orgânicos pela ionização na chama de H₂/ar, gerando corrente elétrica proporcional à concentração",
             "is_correct": True, "alt_text": "Esquema do detector FID com eletrodo de coleta"},
            {"id": "a2", "text": "Medir a absorbância dos compostos na região UV-Vis",
             "is_correct": False, "alt_text": "Detector UV-Vis"},
            {"id": "a3", "text": "Ionizar compostos para análise por espectrometria de massa",
             "is_correct": False, "alt_text": "Fonte de ionização por elétrons"},
            {"id": "a4", "text": "Medir a condutividade térmica dos compostos eluídos",
             "is_correct": False, "alt_text": "Detector TCD"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "O FID queima compostos orgânicos numa chama de H₂/ar; os íons gerados criam corrente elétrica mensurável, altamente sensível a C-H.",
        "system_name": "Cromatografia Gasosa (CG)",
    },
    {
        "type": "MULTIPLA_ESCOLHA", "difficulty": "DIFICIL",
        "text": "Na titulação de Karl Fischer, o que é determinado e qual é o princípio do método?",
        "alternatives": [
            {"id": "a1",
             "text": "Teor de água; reação estequiométrica entre H₂O e o reagente de Karl Fischer (I₂ + SO₂ + base)",
             "is_correct": True, "alt_text": "Titulador Karl Fischer automático"},
            {"id": "a2", "text": "Teor de cloretos; precipitação com nitrato de prata (AgNO₃)",
             "is_correct": False, "alt_text": "Titulação de Mohr"},
            {"id": "a3", "text": "Acidez total; reação de neutralização com hidróxido de sódio",
             "is_correct": False, "alt_text": "Titulação ácido-base"},
            {"id": "a4", "text": "Poder oxidante total; oxidação com permanganato de potássio",
             "is_correct": False, "alt_text": "Titulação com permanganato"},
        ],
        "correct_alternative_id": "a1",
        "explanation": "A titulação de Karl Fischer usa a reação: H₂O + I₂ + SO₂ + RN → [RNH]SO₄R + [RNH]I. É o método padrão para determinação de umidade.",
        "system_name": "Titulação de Karl Fischer",
    },
    {
        "type": "ASSOCIACAO_SISTEMA", "difficulty": "DIFICIL",
        "text": "Associe cada técnica espectroscópica à sua principal aplicação analítica.",
        "alternatives": [],
        "association_pairs": [
            {"material_id": "t1", "material_name": "Espectroscopia de Absorção Atômica (AAS)",
             "target_id": "a1", "target_text": "Determinação de metais em traços em água, solos e alimentos"},
            {"material_id": "t2", "material_name": "Espectroscopia de Emissão de Chama (FES)",
             "target_id": "a2", "target_text": "Quantificação de metais alcalinos (Na, K, Li) em fluidos biológicos"},
            {"material_id": "t3", "material_name": "Espectroscopia de Infravermelho (FTIR)",
             "target_id": "a3", "target_text": "Identificação de grupos funcionais e fingerprint de compostos orgânicos"},
            {"material_id": "t4", "material_name": "Ressonância Magnética Nuclear (RMN)",
             "target_id": "a4", "target_text": "Elucidação da estrutura molecular completa de compostos purificados"},
        ],
        "explanation": "AAS → metais-traço; FES → alcalinos; FTIR → grupos funcionais; RMN → estrutura molecular. Cada técnica tem sensibilidade e seletividade únicas.",
        "system_name": "Técnicas espectroscópicas",
    },
]


# ── Seed functions ─────────────────────────────────────────────────────────────

async def seed_questions(db) -> int:
    """Insere as questões no banco. Retorna o número de questões inseridas."""
    collection = db["questions"]

    existing = await collection.count_documents({})
    if existing >= len(QUESTIONS):
        logger.info(f"Banco já tem {existing} questões (≥ {len(QUESTIONS)}) — pulando seed de questões.")
        return 0

    inserted = 0
    for i, q_data in enumerate(QUESTIONS):
        alts = [Alternative(**a) for a in q_data.get("alternatives", [])]
        pairs = [AssociationPair(**p) for p in q_data.get("association_pairs", [])]
        correct_id = q_data.get("correct_alternative_id") or next(
            (a.id for a in alts if a.is_correct), None
        )

        question = Question(
            type=QuestionType(q_data["type"]),
            difficulty=DifficultyLevel(q_data["difficulty"]),
            text=q_data["text"],
            image_alt_text=q_data.get("image_alt_text"),
            alternatives=alts,
            association_pairs=pairs,
            correct_alternative_id=correct_id,
            explanation=q_data.get("explanation", ""),
            material_name=q_data.get("material_name"),
            system_name=q_data.get("system_name"),
            function_text=q_data.get("function_text"),
            created_by="seed",
            is_active=True,
        )
        await collection.insert_one(question.to_mongo())
        inserted += 1

    logger.info(f"✅ {inserted} questões inseridas no banco.")
    return inserted


async def seed_admin_user(db) -> None:
    """Cria usuário administrador padrão se não existir."""
    users = db["users"]
    existing = await users.find_one({"email": "admin@etec.sp.gov.br"})
    if existing:
        logger.info("Admin já existe — pulando criação.")
        return

    admin = User(
        name="Administrador ETEC",
        email="admin@etec.sp.gov.br",
        hashed_password=hash_password("Admin@2025"),
        role=UserRole.ADMINISTRADOR,
        lgpd_consent=LGPDConsent(accepted=True, guardian_name=None),
        progress=UserProgress(),
    )
    await users.insert_one(admin.to_mongo())
    logger.info("✅ Usuário admin criado: admin@etec.sp.gov.br / Admin@2025")


async def seed_teacher_user(db) -> None:
    """Cria professor de demonstração."""
    users = db["users"]
    existing = await users.find_one({"email": "professor@etec.sp.gov.br"})
    if existing:
        return

    teacher = User(
        name="Prof. Demonstração",
        email="professor@etec.sp.gov.br",
        hashed_password=hash_password("Prof@2025"),
        role=UserRole.PROFESSOR,
        class_name="1Q-A",
        lgpd_consent=LGPDConsent(accepted=True),
        progress=UserProgress(),
    )
    await users.insert_one(teacher.to_mongo())
    logger.info("✅ Professor demo criado: professor@etec.sp.gov.br / Prof@2025")


async def seed_db() -> None:
    """Ponto de entrada principal do seed."""
    mongo_url = (
        f"mongodb://{settings.MONGO_USERNAME}:{settings.MONGO_PASSWORD}"
        f"@{settings.MONGO_HOST}:{settings.MONGO_PORT}"
        f"/{settings.DB_NAME}?authSource=admin"
    )
    client = AsyncIOMotorClient(mongo_url)
    db = client[settings.DB_NAME]

    logger.info("🌱 Iniciando seed do banco de dados LabQuiz ETEC...")
    await seed_questions(db)
    await seed_admin_user(db)
    await seed_teacher_user(db)
    logger.info("🎉 Seed concluído com sucesso!")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed_db())
