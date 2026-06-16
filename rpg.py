"""
RPG Textual — O Reino de Valdória (Expansão Tática & Loot)
Dependência: pip install rich
"""

import time
import random
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.align import Align

# ==============================================================================
# 1. ESTADO GLOBAL E BASE DE DADOS
# ==============================================================================
console = Console()

jogador = {
    "nome": "",
    "vida": 100,
    "energia": 100, 
    "dano_max": 25, 
    "pocoes": 5,
    "amuleto": False,
    "armadura": False,
    "chave": False,
    "concluidos": set(),
    "locais_descobertos": {"Vila"}, 
}

# NOVO: Inimigos agora possuem atributos dinâmicos ('esquiva' e 'armadura')
INIMIGOS_COMUNS = [
    {"nome": "Goblin Saqueador", "vida_min": 20, "vida_max": 30, "dano_max": 12, "esquiva": 30, "armadura": 0},
    {"nome": "Bandido da Estrada", "vida_min": 30, "vida_max": 40, "dano_max": 15, "esquiva": 20, "armadura": 0},
    {"nome": "Aranha Gigante", "vida_min": 25, "vida_max": 35, "dano_max": 18, "esquiva": 10, "armadura": 0},
    {"nome": "Esqueleto Animado", "vida_min": 15, "vida_max": 25, "dano_max": 10, "esquiva": 0, "armadura": 5},
]

LOCAIS = {
    # =========================================================
    # ZONA 1 (Chefe: Lobo) 
    # =========================================================
    "Vila": {"descricao": "A pacata vila de Valdória. O ar é calmo aqui.", "vizinhos": ["Campos de Trigo"]},
    
    "Campos de Trigo": {"descricao": "Campos vastos. Inimigos podem se esconder no mato alto. (Área de Risco)", "vizinhos": ["Vila", "Trilha Estreita"]},
    
    "Trilha Estreita": {"descricao": "O caminho afunila e marcas de garras rasgam o chão.", "inimigo_fixo": "Goblin Saqueador", "vizinhos": ["Campos de Trigo", "Moinho em Ruínas"]},
    
    "Moinho em Ruínas": {
        "descricao": "Um moinho destruído. Há um baú de madeira quase apodrecido no centro.", 
        "vizinhos": ["Trilha Estreita", "Caverna Musgosa"],
        "interacao": {"tipo": "armadilha_bau", "usado": False, "msg": "Você forçou a fechadura! Uma farpa envenenada cortou sua mão (-15 HP), mas você achou 2 Poções!"}
    },

    "Caverna Musgosa": {
        "descricao": "Uma caverna coberta de musgo e úmida, perto de uma cachoeira.", 
        "vizinhos": ["Bosque Nebuloso"],
        "descanso": True # 
    },
    
    "Bosque Nebuloso": {"descricao": "A névoa dificulta a visão. Vultos passam rápido. (Área de Risco)", "vizinhos": ["Moinho em Ruínas", "Entrada da Caverna"]},
    
    "Entrada da Caverna": {"descricao": "O fedor de sangue é forte. Um sentinela guarda o caminho.", "inimigo_fixo": "Aranha Gigante", "vizinhos": ["Bosque Nebuloso", "Floresta Sombria"]},
    
    "Floresta Sombria": {"descricao": "A escuridão total do covil do guardião.", "desafio": "lobo", "vizinhos": ["Estrada de Terra"]},

    # =========================================================
    # ZONA 2 (Chefe: Urso)
    # =========================================================
    "Estrada de Terra": {"descricao": "O caminho é íngreme e perigoso. (Área de Risco)", "vizinhos": ["Floresta Sombria", "Ponte Quebrada"]},
    
    "Ponte Quebrada": {"descricao": "Um bloqueio foi montado aqui com carroças viradas.", "inimigo_fixo": "Bandido da Estrada", "vizinhos": ["Estrada de Terra", "Acampamento Abandonado"]},

    "Abaixo da ponte": {
        "descricao": "Restos de uma fogueira e mochilas de viajantes caídos, parece confortavel.", 
        "vizinhos": ["Ponte Quebrada", "Vale Congelado"],
        "descanso": True,
        "interacao": {"tipo": "pocao", "valor": 1, "usado": False, "msg": "Você achou 1 Poção intacta!"}
    },
    
    "Vale Congelado": {"descricao": "A neve cega seus olhos. Predadores caçam aqui. (Área de Risco)", "vizinhos": ["Acampamento Abandonado", "Caverna Úmida"]},
    
    "Caverna Úmida": {"descricao": "Gelo escorre pelas paredes. Algo cadavérico se levanta da neve.", "inimigo_fixo": "Esqueleto Animado", "vizinhos": ["Vale Congelado", "Montanhas Cinzentas"]},
    
    "Montanhas Cinzentas": {"descricao": "Picos nevados brutais.", "desafio": "urso", "vizinhos": ["Pântano Escuro"]},

    # =========================================================
    # ZONA 3 (Chefe: Orc)
    # =========================================================
    "Pântano Escuro": {"descricao": "Águas turvas e cheiro de podridão. (Área de Risco)", "vizinhos": ["Montanhas Cinzentas", "Trilha Enlameada"]},
    
    "Trilha Enlameada": {"descricao": "Passos pesados afundam na lama em sua direção.", "inimigo_fixo": "Bandido da Estrada", "vizinhos": ["Pântano Escuro", "Altar de Sangue"]},
    
    "Altar de Sangue": {
        "descricao": "Um altar macabro. Inscrições prometem poder em troca de vitalidade.", 
        "vizinhos": ["Trilha Enlameada", "Ruínas Antigas"],
        "interacao": {"tipo": "sacrificio", "usado": False, "msg": "Você derramou seu sangue no altar (-20 HP). Sua força física aumentou permanentemente (+5 Dano) e 2 Poções surgiram!"}
    },
    
    "Ruínas Antigas": {"descricao": "Restos de uma muralha quebrada. (Área de Risco)", "vizinhos": ["Altar de Sangue", "Portões do Forte"]},

    "Acampamento Abandonado": {
        "descricao": "Restos de uma fogueira e mochilas de viajantes caídos.", 
        "vizinhos": [ "Portões do Forte"],
        "descanso": True,
        "interacao": {"tipo": "pocao", "valor": 1, "usado": False, "msg": "Você achou 1 Poção intacta!"}
    },
    
    "Portões do Forte": {"descricao": "Um guarda morto-vivo protege a entrada da fortaleza.", "inimigo_fixo": "Esqueleto Animado", "vizinhos": ["Ruínas Antigas", "Forte Abandonado"]},
    
    "Forte Abandonado": {"descricao": "Ruínas de um forte militar tomado por brutalidade.", "desafio": "orc", "vizinhos": ["Covil do Dragão"]},
    
    "Covil do Dragão": {"descricao": "As portas de pedra do covil emanam calor infernal.", "desafio": "dragao"},
}

# ==============================================================================
# 2. CAMADA DE APRESENTAÇÃO (UI)
# ==============================================================================
def limpar():
    console.clear()

def narrar(texto, estilo="white"):
    for letra in texto:
        console.print(letra, end="", style=estilo)
        if letra in ".!?": time.sleep(0.4)
        elif letra in ",;:": time.sleep(0.2)
        else: time.sleep(0.02)
    console.print()

def gerar_barra_vida(vida_atual, vida_max, cor_preenchida="green"):
    tamanho_barra = 20
    vida_normalizada = max(0, min(vida_atual, vida_max))
    blocos_preenchidos = int((vida_normalizada / vida_max) * tamanho_barra)
    blocos_vazios = tamanho_barra - blocos_preenchidos
    return f"[{cor_preenchida}]{'█' * blocos_preenchidos}[/][dim]{'░' * blocos_vazios}[/]"

def mostrar_hud_combate(inimigo):
    print()
    tabela = Table.grid(expand=True)
    tabela.add_column(justify="left", ratio=2)
    tabela.add_column(justify="center", ratio=1)
    tabela.add_column(justify="right", ratio=2)
    
    barra_jogador = gerar_barra_vida(jogador["vida"], 100, "green")
    barra_inimigo = gerar_barra_vida(inimigo["vida"], inimigo["vida_max"], "red")

    # NOVO: O HUD agora mostra a quantidade de poções
    info_jogador = f"[bold cyan]{jogador['nome']}[/]\n{barra_jogador}\n[green]❤ {jogador['vida']}/100 HP[/]\n[bold green]🧪 Poções: {jogador['pocoes']}[/]"
    info_inimigo = f"[bold red]{inimigo['nome']}[/]\n{barra_inimigo}\n[red]❤ {inimigo['vida']}/{inimigo['vida_max']} HP[/]"
    
    if inimigo.get("carregando_ataque"):
        info_inimigo += "\n[bold yellow blink]⚠ PREPARANDO GOLPE![/]"

    tabela.add_row(info_jogador, "\n[bold yellow]⚔ VS ⚔[/]", info_inimigo)
    console.print(Panel(tabela, border_style="red", title="[bold white]EM COMBATE[/]"))

def mostrar_status():
    tabela = Table(title=f"Status de {jogador['nome']}", style="cyan")
    tabela.add_column("Atributo", justify="right", style="cyan", no_wrap=True)
    tabela.add_column("Valor", style="magenta")

    cor_vida = "green" if jogador["vida"] > 50 else "red"
    tabela.add_row("❤ Vida", f"[{cor_vida}]{jogador['vida']}/100[/]")
    tabela.add_row("🧪 Poções", f"[green]{jogador['pocoes']}[/]")
    tabela.add_row("✦ Amuleto", "[gold1]Equipado[/]" if jogador["amuleto"] else "[dim]Vazio[/]")
    tabela.add_row("🛡 Armadura", "[grey74]Equipada[/]" if jogador["armadura"] else "[dim]Vazio[/]")
    tabela.add_row("🗝 Chave", "[yellow]Equipada[/]" if jogador["chave"] else "[dim]Vazio[/]")

    cor_energia = "yellow" if jogador["energia"] > 30 else "red"
    tabela.add_row("⚡ Energia", f"[{cor_energia}]{jogador['energia']}/100[/]")

    console.print(Align.center(tabela))
    Prompt.ask("\n[dim]Pressione ENTER para continuar[/]")

def tela_titulo():
    limpar()
    titulo_ascii = (
        "[bold gold1]"
" ██████╗      ██████╗ █████╗ ██╗   ██╗ █████╗ ██╗     ███████╗██╗██████╗  ██████╗\n"
"██╔═══██╗    ██╔════╝██╔══██╗██║   ██║██╔══██╗██║     ██╔════╝██║██╔══██╗██║   ██║\n"
"██║   ██║    ██║     ███████║██║   ██║███████║██║     █████╗  ██║██████╔╝██║   ██║\n"
"██║   ██║    ██║     ██╔══██║╚██╗ ██╔╝██╔══██║██║     ██╔══╝  ██║██╔══██╗██║   ██║\n"
"╚██████╔╝    ╚██████╗██║  ██║ ╚████╔╝ ██║  ██║███████╗███████╗██║██║  ██║╚██████╔╝\n"
" ╚═════╝      ╚═════╝╚═╝  ╚═╝  ╚═══╝  ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝╚═╝  ╚═╝ ╚═════╝\n"

"██████╗  █████╗ ███████╗   ██████╗ ██╗   ██╗ █████╗ ████████╗██████╗  ██████╗\n"
"██╔══██╗██╔══██╗██╔════╝  ██╔═══██╗██║   ██║██╔══██╗╚══██╔══╝██╔══██╗██╔═══██╗\n"
"██║  ██║███████║███████╗  ██║   ██║██║   ██║███████║   ██║   ██████╔╝██║   ██║\n"
"██║  ██║██╔══██║╚════██║  ██║▄▄ ██║██║   ██║██╔══██║   ██║   ██╔══██╗██║   ██║\n"
"██████╔╝██║  ██║███████║  ╚██████╔╝╚██████╔╝██║  ██║   ██║   ██║  ██║╚██████╔╝\n"
"╚═════╝ ╚═╝  ╚═╝╚══════╝   ╚══▀▀═╝  ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝\n"

"██████╗ ██████╗  ██████╗ ██╗   ██╗ █████╗  ██████╗ ██████╗ ███████╗███████╗\n"
"██╔══██╗██╔══██╗██╔═══██╗██║   ██║██╔══██╗██╔════╝██╔═══██╗██╔════╝██╔════╝\n"
"██████╔╝██████╔╝██║   ██║██║   ██║███████║██║     ██║   ██║█████╗  ███████╗\n"
"██╔═══╝ ██╔══██╗██║   ██║╚██╗ ██╔╝██╔══██║██║     ██║   ██║██╔══╝  ╚════██║\n"
"██║     ██║  ██║╚██████╔╝ ╚████╔╝ ██║  ██║╚██████╗╚██████╔╝███████╗███████║\n"
"╚═╝     ╚═╝  ╚═╝ ╚═════╝   ╚═══╝  ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝╚══════╝\n"
        "[/]"
    )
    painel = Panel(Align.center(f"{titulo_ascii}\n[white]⚔ Aventura em Valdória ⚔[/]"), border_style="gold1", padding=(1, 2))
    console.print(painel)
    return Prompt.ask("\n[bold]Pressione ENTER para jogar | 'P' para pular[/]").lower() == "p"

# ==============================================================================
# 3. MOTOR DE COMBATE (EXPANDIDO)
# ==============================================================================
def combate_comum(nome_inimigo_fixo=None):
    """
    Gerencia combates comuns. Se 'nome_inimigo_fixo' for passado, 
    busca exatamente aquele inimigo no banco de dados. Caso contrário, sorteia.
    """
    if nome_inimigo_fixo:
        # Busca o molde exato na lista através de uma List Comprehension
        molde = next(inimigo for inimigo in INIMIGOS_COMUNS if inimigo["nome"] == nome_inimigo_fixo)
    else:
        # Sorteio aleatório original
        molde = random.choice(INIMIGOS_COMUNS)
        
    vida_rolada = random.randint(molde["vida_min"], molde["vida_max"])
    
    inimigo = {
        "nome": molde["nome"],
        "vida": vida_rolada,
        "vida_max": vida_rolada,
        "dano_max": molde["dano_max"],
        "esquiva": molde["esquiva"],
        "armadura": molde["armadura"],
        "carregando_ataque": False
    }

    limpar()
    console.print(Panel(f"[bold red]Um {inimigo['nome']} saltou das sombras![/]", border_style="red"))
    time.sleep(1)

    while inimigo["vida"] > 0 and jogador["vida"] > 0:
        jogador_defendendo = False # Reseta a defesa do jogador todo turno
        mostrar_hud_combate(inimigo)

        # Menu Expandido
        menu_acoes = (
            "[bold cyan]1.[/] Atacar Rápido (85% acerto)\n"
            "[bold cyan]2.[/] Ataque Pesado (50% acerto, Muito Dano)\n"
            "[bold cyan]3.[/] Defender (-50% dano recebido)\n"
            "[bold cyan]4.[/] Usar Poção (Recupera 30 HP)\n"
            "[bold cyan]5.[/] Fugir (50% chance)"
        )
        console.print(Panel(menu_acoes, title="Ações Táticas", border_style="cyan"))
        
        escolha = Prompt.ask("Sua escolha", choices=["1", "2", "3", "4", "5"])

        # -----------------------------------------------------
        # PROCESSAMENTO DAS AÇÕES DO JOGADOR
        # -----------------------------------------------------
        if escolha == "5": # FUGIR
            if random.randint(1, 100) >= 50:
                console.print("\n[bold yellow]💨 Você despistou o inimigo e fugiu![/]")
                time.sleep(1.5)
                return False 
            console.print("\n[bold red]❌ Você tropeçou tentando fugir![/]")

        elif escolha == "4": # POÇÃO
            if jogador["pocoes"] > 0:
                jogador["pocoes"] -= 1
                jogador["vida"] = min(100, jogador["vida"] + 30)
                console.print("\n[bold green]🧪 Você bebeu uma poção e recuperou 30 HP![/]")
            else:
                console.print("\n[bold red]❌ Você não tem poções! O tempo de procurar na bolsa abriu sua guarda![/]")

        elif escolha == "3": # DEFENDER
            jogador_defendendo = True
            console.print("\n[bold blue]🛡 Você ergueu seu escudo e assumiu uma postura rígida![/]")

        elif escolha in ["1", "2"]: # ATAQUES
            chance_base = 85 if escolha == "1" else 50
            
            # Testa se o jogador acertou o golpe
            if random.randint(1, 100) <= chance_base:
                
                # Testa se o inimigo esquivou (Atributo Dinâmico)
                if random.randint(1, 100) <= inimigo["esquiva"]:
                    console.print(f"\n[cyan]⚔[/] Você atacou, mas o [bold yellow]{inimigo['nome']} ESQUIVOU[/] do golpe!")
                else:
                    dano = random.randint(5, jogador["dano_max"])
                    if escolha == "2": # Ataque pesado causa 50% a mais
                        dano = int(dano * 1.5) 
                        console.print("\n[bold red]💥 ACERTOU EM CHEIO![/]")
                    
                    # Redução pela armadura do inimigo
                    dano_causado = max(1, dano - inimigo["armadura"])
                    inimigo["vida"] -= dano_causado
                    console.print(f"[cyan]⚔[/] Você causou [bold green]{dano_causado}[/] de dano!")
            else:
                console.print("\n[cyan]⚔[/] Você balançou a espada e [bold red]ERROU[/]!")

        time.sleep(1.5)

        # -----------------------------------------------------
        # CONDIÇÃO DE VITÓRIA E LOOT (CICLO DE RECOMPENSA)
        # -----------------------------------------------------
        if inimigo["vida"] <= 0:
            mostrar_hud_combate(inimigo)
            console.print(f"\n✨ [bold gold1]Você derrotou o {inimigo['nome']}![/]")
            
            # 40% de chance de dropar poção
            if random.randint(1, 100) <= 40:
                jogador["pocoes"] += 1
                console.print(Panel("[bold green]🧪 Você encontrou uma Poção de Vida nos restos do inimigo![/]", border_style="green", expand=False))
            
            Prompt.ask("\n[dim]Pressione ENTER para continuar[/]")
            return True

        # -----------------------------------------------------
        # TURNO E INTELIGÊNCIA DO INIMIGO
        # -----------------------------------------------------
        console.print("\n[dim]O inimigo reage...[/]")
        time.sleep(0.8)

        # Se ele estava carregando ataque no turno anterior, ele descarrega agora
        if inimigo["carregando_ataque"]:
            inimigo["carregando_ataque"] = False
            dano_inimigo = inimigo["dano_max"] + 15 # Dano devastador
            console.print(f"[bold red blink]💥 O {inimigo['nome']} desfere seu GOLPE BRUTAL![/]")
            
        else:
            # 20% de chance de telegrafar um ataque para o PRÓXIMO turno
            if random.randint(1, 100) <= 20:
                inimigo["carregando_ataque"] = True
                console.print(f"[bold yellow blink]⚠ O {inimigo['nome']} recua e começa a preparar um ataque devastador![/]")
                time.sleep(2)
                limpar()
                continue # Termina o turno do inimigo aqui (ele não causa dano agora)
            
            # Ataque Normal
            dano_inimigo = random.randint(3, inimigo["dano_max"])
            if random.randint(1, 100) > 80:
                console.print(f"[red]🛡[/] O {inimigo['nome']} atacou, mas [bold green]ERROU![/]\n")
                dano_inimigo = 0

        # Aplicação final de dano se o inimigo não errou ou não está carregando
        if dano_inimigo > 0:
            if jogador_defendendo:
                dano_inimigo = dano_inimigo // 2 # Corta o dano pela metade
                console.print("[blue]Sua postura defensiva absorveu grande parte do impacto![/]")
                
            if jogador["armadura"]:
                dano_inimigo = max(0, dano_inimigo - 5) 

            jogador["vida"] -= dano_inimigo
            console.print(f"[red]🛡[/] Você sofreu [bold red]{dano_inimigo}[/] de dano!\n")

        time.sleep(2.5) 
        limpar()

    if jogador["vida"] <= 0:
        mostrar_hud_combate(inimigo)
        console.print("\n[bold red blink]💀 VOCÊ MORREU![/]")
        exit(0)

def checar_encontro_aleatorio(id_sala):
    if id_sala == "Vila": return 
    if random.random() <= 0.35: 
        limpar()
        narrar("Você ouve algo se aproximando...", "bold yellow")
        combate_comum()

# ==============================================================================
# 4. EVENTOS ESPECIAIS (CHEFES) 
# ==============================================================================
def combate_chefe(stats_chefe, chave_recompensa, texto_recompensa, cor_recompensa):
    """
    Motor universal para batalhas de chefe.
    Reutiliza a lógica tática do combate comum, mas aplica restrições pesadas (sem fuga).
    """
    # Cria uma cópia do dicionário para não alterar os status base acidentalmente
    inimigo = stats_chefe.copy()
    inimigo["vida_max"] = inimigo["vida"]
    inimigo["carregando_ataque"] = False

    limpar()
    console.print(Panel(f"[bold red]🔥 O GUARDIÃO {inimigo['nome'].upper()} DESPERTA! 🔥[/]", border_style="red"))
    time.sleep(2)

    while inimigo["vida"] > 0 and jogador["vida"] > 0:
        jogador_defendendo = False
        mostrar_hud_combate(inimigo)

        # O menu de chefe é levemente diferente (Fugir está desabilitado na prática)
        menu_acoes = (
            "[bold cyan]1.[/] Atacar Rápido\n"
            "[bold cyan]2.[/] Ataque Pesado\n"
            "[bold cyan]3.[/] Defender\n"
            "[bold cyan]4.[/] Usar Poção\n"
            "[dim]5. Fugir (Bloqueado)[/]"
        )
        console.print(Panel(menu_acoes, title="Ações de Chefe", border_style="red"))
        
        escolha = Prompt.ask("Sua escolha", choices=["1", "2", "3", "4", "5"])

        # -----------------------------------------------------
        # PROCESSAMENTO DO JOGADOR
        # -----------------------------------------------------
        if escolha == "5":
            console.print("\n[bold red blink]❌ A arena está trancada! Não há como fugir de um Chefe![/]")
            time.sleep(2)
            limpar()
            continue # Reinicia o turno do jogador, ele não perde a vez por tentar fugir

        elif escolha == "4":
            if jogador["pocoes"] > 0:
                jogador["pocoes"] -= 1
                jogador["vida"] = min(100, jogador["vida"] + 30)
                console.print("\n[bold green]🧪 Você bebeu uma poção e recuperou 30 HP![/]")
            else:
                console.print("\n[bold red]❌ Sem poções! O chefe avança enquanto você procurava na bolsa![/]")

        elif escolha == "3":
            jogador_defendendo = True
            console.print("\n[bold blue]🛡 Você firma os pés no chão, preparando-se para o impacto![/]")

        elif escolha in ["1", "2"]:
            chance_base = 85 if escolha == "1" else 50
            
            if random.randint(1, 100) <= chance_base:
                if random.randint(1, 100) <= inimigo.get("esquiva", 0):
                    console.print(f"\n[cyan]⚔[/] Você atacou, mas o [bold yellow]{inimigo['nome']} ESQUIVOU[/] agilmente!")
                else:
                    dano = random.randint(5, jogador["dano_max"])
                    if escolha == "2": 
                        dano = int(dano * 1.5) 
                        console.print("\n[bold red]💥 ACERTOU EM CHEIO![/]")
                    
                    dano_causado = max(1, dano - inimigo.get("armadura", 0))
                    inimigo["vida"] -= dano_causado
                    console.print(f"[cyan]⚔[/] Você causou [bold green]{dano_causado}[/] de dano ao chefe!")
            else:
                console.print("\n[cyan]⚔[/] Sob a pressão do combate, você [bold red]ERROU[/] o ataque!")

        time.sleep(1.5)

        # -----------------------------------------------------
        # CONDIÇÃO DE VITÓRIA DO CHEFE
        # -----------------------------------------------------
        if inimigo["vida"] <= 0:
            mostrar_hud_combate(inimigo)
            console.print(f"\n✨ [bold gold1]O {inimigo['nome']} tomba perante sua lâmina![/]")
            
            if chave_recompensa: # Atribui o item chave ao jogador
                jogador[chave_recompensa] = True
                console.print(Panel(f"[{cor_recompensa}]{texto_recompensa}[/]", title=f"✓ ITEM ÉPICO OBTIDO", border_style=cor_recompensa))
            
            Prompt.ask("\n[dim]Pressione ENTER para continuar[/]")
            return True

        # -----------------------------------------------------
        # TURNO DO CHEFE (IA Dinâmica)
        # -----------------------------------------------------
        console.print("\n[dim]O Chefe reage...[/]")
        time.sleep(0.8)

        if inimigo["carregando_ataque"]:
            inimigo["carregando_ataque"] = False
            dano_inimigo = inimigo["dano_max"] + 25 # Dano de chefe é mais punitivo
            console.print(f"[bold red blink]💥 O {inimigo['nome']} ANQUILA TUDO À FRENTE COM SEU GOLPE![/]")
        else:
            # Chefes têm uma chance específica de telegrafar (definida no dict)
            chance_telegrafar = inimigo.get("chance_telegrafar", 20)
            if random.randint(1, 100) <= chance_telegrafar:
                inimigo["carregando_ataque"] = True
                console.print(f"[bold yellow blink]⚠ O {inimigo['nome']} brilha com energia letal... PREPARE-SE![/]")
                time.sleep(2)
                limpar()
                continue
            
            dano_inimigo = random.randint(10, inimigo["dano_max"]) # Chefes nunca dão dano baixo
            if random.randint(1, 100) > 85: # Chefes erram menos (apenas 15% de chance)
                console.print(f"[red]🛡[/] O {inimigo['nome']} atacou rápido demais e [bold green]ERROU![/]\n")
                dano_inimigo = 0

        if dano_inimigo > 0:
            if jogador_defendendo:
                dano_inimigo = dano_inimigo // 2 
                console.print("[blue]Seu escudo rangeu, mas absorveu o pior do golpe![/]")
                
            if jogador["armadura"]:
                dano_inimigo = max(0, dano_inimigo - 5) 

            jogador["vida"] -= dano_inimigo
            console.print(f"[red]🛡[/] O Chefe dilacerou sua defesa, causando [bold red]{dano_inimigo}[/] de dano!\n")

        time.sleep(2.5) 
        limpar()

    if jogador["vida"] <= 0:
        mostrar_hud_combate(inimigo)
        console.print("\n[bold red blink]💀 A ESPERANÇA MORREU COM VOCÊ...[/]")
        exit(0)

# ==============================================================================
# DICIONÁRIOS DE CHEFES (Data Injection) E CHAMADAS
# ==============================================================================

def desafio_lobo():
    narrar("Um uivo congela sua espinha. O alfa saltou da escuridão!", "bold yellow")
    lobo_stats = {"nome": "Lobo Alfa", "vida": 60, "dano_max": 25, "esquiva": 10, "armadura": 0, "chance_telegrafar": 15}
    combate_chefe(lobo_stats, "amuleto", "Amuleto Encantado: Protege contra as chamas.", "gold1")

def desafio_urso():
    narrar("A nevasca revela uma silhueta colossal. O predador supremo das montanhas!", "bold yellow")
    urso_stats = {"nome": "Urso Colossal", "vida": 80, "dano_max": 30, "esquiva": 0, "armadura": 0, "chance_telegrafar": 30}
    combate_chefe(urso_stats, "armadura", "Armadura de Gelo: Reforça sua defesa corporal.", "grey74")

def desafio_orc():
    narrar("Os portões são chutados. Um Orc de dois metros e machado ensanguentado ruge!", "bold yellow")
    orc_stats = {"nome": "Orc Senhor da Guerra", "vida": 100, "dano_max": 35, "esquiva": 15, "armadura": 15, "chance_telegrafar": 40}
    combate_chefe(orc_stats, "chave", "Chave de Obsidiana: Destranca os portões do vulcão.", "yellow")

def desafio_dragao():
    # O Dragão só pode ser enfrentado se o jogador explorou e venceu os outros chefes
    if not (jogador["amuleto"] and jogador["armadura"] and jogador["chave"]):
        console.print(Panel("[bold red]O calor da porta do Covil derrete sua pele. Você precisa do Amuleto, da Armadura e da Chave para sobreviver aqui![/]", border_style="red"))
        Prompt.ask("\n[dim]Pressione ENTER para recuar...[/]")
        return False # Impede a luta e volta pro loop principal

    limpar()
    narrar("Você insere a chave. A armadura protege do calor. O amuleto dissipa a magia negra...", "bold cyan")
    narrar("Ignaroth emerge do magma. O destino de Valdória será selado agora!", "bold red")
    
    dragao_stats = {"nome": "Ignaroth, o Dragão", "vida": 150, "dano_max": 40, "esquiva": 0, "armadura": 15, "chance_telegrafar": 50}
    
    # Dragão não dropa item, ele finaliza o jogo
    venceu = combate_chefe(dragao_stats, None, None, None)
    
    if venceu:
        limpar()
        console.print(Panel("[bold gold1]O enorme dragão desaba, transformando-se em cinzas. Você recuperou a Pedra do Fogo! O inverno eterno acabou.\n\nPARABÉNS, CAVALEIRO! VOCÊ ZEROU O JOGO![/]", padding=(2, 4), border_style="gold1"))
        exit(0)

# ==============================================================================
# 5. LOOP DE EXPLORAÇÃO (MOTOR PRINCIPAL)
# ==============================================================================
def explorar():
    sala_atual = "Vila"

    while True:
        limpar()
        dados_da_sala = LOCAIS[sala_atual]
        
        console.print(Panel(f"[italic]{dados_da_sala.get('descricao', '')}[/]", title=f"📍 {sala_atual}", border_style="green"))

        tem_chefe = "desafio" in dados_da_sala and dados_da_sala["desafio"] not in jogador["concluidos"]
        if tem_chefe:
            console.print("[bold blink red]⚠ A atmosfera é sufocante. O Covil do Chefe aguarda![/]\n")

        # -----------------------------------------------------
        # CONSTRUÇÃO DO MENU COM 'FOG OF WAR'
        # -----------------------------------------------------
        menu = Table.grid(padding=(0, 2))
        rotas = dados_da_sala.get("vizinhos", [])
        opcoes_validas = []
        
        for index, destino in enumerate(rotas, 1):
            # Lógica do Fog of War: Se não descobriu, oculta o nome
            if destino in jogador["locais_descobertos"]:
                nome_exibicao = f"Caminhar para {destino}"
            else:
                nome_exibicao = "Explorar Caminho Desconhecido"
                
            menu.add_row(f"[bold cyan]{index}.[/]", nome_exibicao)
            opcoes_validas.append(str(index))
            
        menu.add_row("", "") 
        
        # Opção de Interação (Eventos únicos)
        tem_interacao = "interacao" in dados_da_sala and not dados_da_sala["interacao"]["usado"]
        if tem_interacao:
            menu.add_row("[bold magenta]I.[/]", "Investigar o Local")
            opcoes_validas.extend(["i", "I"])

        # Opção de Descanso (Apenas em Safe Zones)
        if dados_da_sala.get("descanso"):
            menu.add_row("[bold blue]D.[/]", "Descansar e recuperar Energia")
            opcoes_validas.extend(["d", "D"])

        menu.add_row("[bold yellow]0.[/]", "Ver status")
        menu.add_row("[bold red]S.[/]", "Sair do jogo")
        opcoes_validas.extend(["0", "s", "S"])

        console.print(menu)
        escolha = Prompt.ask("\n[bold cyan]O que deseja fazer?[/]", choices=opcoes_validas).upper()

        # -----------------------------------------------------
        # PROCESSAMENTO DE AÇÕES DE SISTEMA / SALA
        # -----------------------------------------------------
        if escolha == "0":
            mostrar_status()
            continue 
            
        if escolha == "S":
            console.print("\n[bold italic green]Sua jornada pausa aqui. Até a próxima![/]")
            break 
            
        if escolha == "D":
            limpar()
            jogador["energia"] = 100
            console.print(Panel("[bold blue]Você monta acampamento, come uma ração seca e dorme algumas horas. Sua energia foi totalmente restaurada.[/]", border_style="blue"))
            Prompt.ask("\n[dim]Pressione ENTER para acordar e continuar[/]")
            continue

        if escolha == "I":
            evento = dados_da_sala["interacao"]
            evento["usado"] = True 
            
            # (Mantém sua lógica de interação: bau, poção, sacrifício, etc)
            if evento["tipo"] == "armadilha_bau":
                jogador["vida"] -= 15
                jogador["pocoes"] += 2
            elif evento["tipo"] == "pocao":
                jogador["pocoes"] += evento["valor"]
            
            console.print(f"\n[bold magenta]✨ {evento['msg']}[/]")
            if jogador["vida"] <= 0:
                console.print("\n[bold red blink]💀 VOCÊ MORREU POR CAUSA DOS FERIMENTOS![/]")
                exit(0)
            Prompt.ask("\n[dim]Pressione ENTER para continuar[/]")
            continue 

        # -----------------------------------------------------
        # LÓGICA DE MOVIMENTAÇÃO: ENERGIA E TEXTOS DE VIAGEM
        # -----------------------------------------------------
        indice_lista = int(escolha) - 1
        proxima_sala = rotas[indice_lista]
        
        limpar()
        
        # 1. Aplica o Custo de Energia (Penalidade se exausto)
        custo_viagem = 10
        if jogador["energia"] >= custo_viagem:
            jogador["energia"] -= custo_viagem
            narrar(f"Você caminha arduamente. O cansaço aumenta... (-10 Energia)[/]")
        else:
            jogador["vida"] -= 15 # Dano por exaustão
            jogador["energia"] = 0
            narrar(f"[bold red blink]Você se arrasta pelo caminho, exausto e machucado! (-15 Vida por Exaustão)[/]")
            if jogador["vida"] <= 0:
                console.print("\n[bold red blink]💀 SEU CORPO CEDEU À EXAUSTÃO. VOCÊ MORREU NO CAMINHO![/]")
                exit(0)
                
        time.sleep(1) # Simula o tempo de transição

        # 2. Descobre a nova sala no Fog of War
        if proxima_sala not in jogador["locais_descobertos"]:
            jogador["locais_descobertos"].add(proxima_sala)
            console.print(f"\n[bold gold1]🗺  Você descobriu um novo local: {proxima_sala}![/]")
            time.sleep(1.5)

        # 3. Transição de Dados
        sala_atual = proxima_sala
        dados_da_nova_sala = LOCAIS.get(sala_atual, {})

        # -----------------------------------------------------
        # LÓGICA DE GATILHOS DE COMBATE (MANTIDA IGUAL)
        # -----------------------------------------------------
        chefes_mapa = {"lobo": desafio_lobo, "urso": desafio_urso, "orc": desafio_orc, "dragao": desafio_dragao}
        chefe_novo = dados_da_nova_sala.get("desafio")
        inimigo_fixo = dados_da_nova_sala.get("inimigo_fixo")
        
        if chefe_novo and chefe_novo not in jogador["concluidos"]:
            if chefe_novo in chefes_mapa:
                chefes_mapa[chefe_novo]()
                jogador["concluidos"].add(chefe_novo)
                
        elif inimigo_fixo and f"fixo_{sala_atual}" not in jogador["concluidos"]:
            venceu = combate_comum(nome_inimigo_fixo=inimigo_fixo)
            if venceu:
                jogador["concluidos"].add(f"fixo_{sala_atual}")
                
        else:
            checar_encontro_aleatorio(sala_atual)

# ==============================================================================
# INICIALIZAÇÃO DA APLICAÇÃO
# ==============================================================================
if __name__ == "__main__":
    pulou_historia = tela_titulo()
    
    if not pulou_historia:
        narrar(
            "No reino de Valdória, o sol não nascia havia três invernos. A Pedra do Fogo — artefato sagrado que aquecia as estações — havia sido roubada por Ignathar, um dragão ancestral que a escondia no fundo da Floresta Sombria, guardada por criaturas que não deixavam ninguém passar.\n\n"
            "Uma profecia antiga dizia que só um cavaleiro de coração verdadeiro poderia atravessar a floresta, vencer os guardiões e recuperar a Pedra do covil do dragão. Muitos tentaram. Nenhum voltou.\n\n"
            "O Rei Aldric convocou você ao salão do trono numa manhã cinza. Sem fanfarra, sem discurso.\n"
            "'Você é o último', disse ele. 'Vá.'\n\n"
            "O cavaleiro colocou a mão no peito, curvou a cabeça — e partiu sozinho rumo ao desconhecido."
        )
        
    jogador["nome"] = Prompt.ask("\n[bold]Nome do cavaleiro[/]", default="Herói")
    explorar()