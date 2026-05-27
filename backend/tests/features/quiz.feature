# language: pt
Funcionalidade: Jogo de Quiz Educacional

  Como aluno do 1º ano de Química
  Quero jogar o quiz sobre materiais laboratoriais
  Para aprender identificar equipamentos e suas funções

  Contexto:
    Dado que estou autenticado como aluno
    E existem questões cadastradas no banco para todos os níveis

  Cenário: Aluno completa quiz fácil com ≥70% e desbloqueia nível médio
    Dado que acesso o nível "FACIL"
    Quando inicio uma sessão de quiz
    E respondo 7 ou mais questões corretamente em 10 perguntas
    E finalizo o quiz
    Então minha precisão deve ser maior ou igual a 70%
    E o nível "MEDIO" deve ser desbloqueado no meu perfil
    E o resultado deve exibir "Nível Médio desbloqueado!"

  Cenário: Aluno falha no quiz fácil com <70% e permanece bloqueado
    Dado que acesso o nível "FACIL"
    Quando inicio uma sessão de quiz
    E respondo menos de 7 questões corretamente em 10 perguntas
    E finalizo o quiz
    Então minha precisão deve ser menor que 70%
    E o nível "MEDIO" deve permanecer bloqueado
    E o resultado deve exibir "Continue praticando para desbloquear o próximo nível"

  Cenário: Aluno usa ajuda "Eliminar 2 Alternativas" e perde pontos
    Dado que tenho uma sessão de quiz ativa
    E a questão atual possui 4 alternativas
    Quando solicito a ajuda "ELIMINATE_TWO"
    Então 2 alternativas incorretas devem ser eliminadas
    E minha pontuação atual deve ser reduzida em 5 pontos
    E o contador de ajudas disponíveis deve ser decrementado em 1

  Cenário: Aluno tenta usar mais ajudas do que o limite permitido
    Dado que tenho uma sessão de quiz ativa
    E já usei o número máximo de ajudas permitidas (2)
    Quando solicito uma ajuda adicional
    Então devo receber um erro "Limite de ajudas atingido para este quiz"
    E minha pontuação não deve ser alterada

  Cenário: Professor cadastra nova questão de múltipla escolha
    Dado que estou autenticado como professor
    Quando envio uma nova questão com tipo "MULTIPLA_ESCOLHA", dificuldade "FACIL"
    E informo 4 alternativas com exatamente 1 correta
    E informo a explicação pedagógica da questão
    Então a questão deve ser salva com status ativo
    E deve aparecer na listagem de questões do sistema

  Cenário: Aluno tenta acessar nível bloqueado diretamente
    Dado que meu perfil possui apenas o nível "FACIL" desbloqueado
    Quando tento iniciar um quiz no nível "MEDIO"
    Então devo receber um erro 403 com mensagem "Nível Médio ainda não desbloqueado"

  Cenário: Aluno visualiza histórico de partidas
    Dado que completei 3 quizzes anteriores
    Quando acesso meu histórico
    Então devo ver 3 sessões listadas com data, nível, pontuação e precisão
