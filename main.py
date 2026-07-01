import flet as ft
import math
import time
import threading
import sqlite3

class MonitoramentoAppMobile:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Monitoramento Escolar Mobile"
        self.page.theme_mode = ft.ThemeMode.SYSTEM
        
        # Dimensões exatas de smartphone para simulação no computador
        self.page.window.width = 410
        self.page.window.height = 730
        
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.page.scroll = ft.ScrollMode.AUTO
        
        # INICIALIZAÇÃO DO BANCO DE DADOS LOCAL
        self.conexao = sqlite3.connect("dados_escola.db", check_same_thread=False)
        self.criar_tabelas_banco()
        
        # BANCO DE MEMÓRIA INTERNO DO APP (Carregado do Banco de Dados)
        self.dados_turmas = {}  
        self.historico_diario = {}  
        
        # Variáveis e vetores de controle originais
        self.fase_onda = 0.0
        self.baterias_animar = []
        self.bateria_geral_animar = None
        self.lista_alunos_dados = []
        self.animacao_ativa = True

        # Inicia a Thread responsável pelo loop contínuo de animação das ondas
        self.thread_ondas = threading.Thread(target=self.loop_animacao_ondas, daemon=True)
        self.thread_ondas.start()

        self.tela_inicial()

    def criar_tabelas_banco(self):
        cursor = self.conexao.cursor()
        # Cria a tabela de alunos se ela não existir
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alunos (
                chave_turma TEXT, idx INTEGER, nome TEXT, atividades TEXT,
                aprendizado TEXT, frequencia TEXT, comportamento TEXT, obs TEXT,
                PRIMARY KEY (chave_turma, idx)
            )
        """)
        # Cria a tabela do diário histórico se ela não existir
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT, chave_turma TEXT,
                data TEXT, atividade TEXT, pagina TEXT, participantes TEXT
            )
        """)
        self.conexao.commit()
    def tela_inicial(self):
        self.page.controls.clear()
        self.page.floating_action_button = None
        self.baterias_animar.clear()
        self.bateria_geral_animar = None
        
        badge = ft.Container(
            content=ft.Text("GESTÃO ACADÊMICA MOBILE", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
            bgcolor=ft.Colors.BLUE_50,
            padding=ft.padding.symmetric(horizontal=12, vertical=5),
            border_radius=6,
            margin=ft.margin.only(top=20, bottom=15)
        )
        
        lbl_titulo = ft.Text("DIÁRIO DO PROFESSOR", size=26, weight=ft.FontWeight.BOLD, font_family="Segoe UI")
        lbl_sub = ft.Text("Selecione uma ferramenta", size=13, color=ft.Colors.GREY_600, font_family="Segoe UI", margin=ft.margin.only(bottom=20))
        
        lbl_sec1 = ft.Container(
            content=ft.Text("MONITORAMENTO DE TURMAS", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_600),
            alignment=ft.alignment.center_left,
            padding=ft.padding.only(left=15, top=5, bottom=5)
        )
        
        botoes_anos = []
        for ano in ["1º Ano", "2º Ano", "3º Ano"]:
            botoes_anos.append(
                ft.ElevatedButton(
                    text=f"Acessar {ano}", width=280, height=45,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                    on_click=lambda e, a=ano: self.tela_turmas(a, objetivo="monitoramento")
                )
            )
            
        lbl_sec2 = ft.Container(
            content=ft.Text("PLANEJAMENTO & DIÁRIO", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_600),
            alignment=ft.alignment.center_left,
            padding=ft.padding.only(left=15, top=15, bottom=5)
        )
        
        btn_lembrete = ft.ElevatedButton(
            text="📌 Lembrete do Professor", width=280, height=42, bgcolor=ft.Colors.BLUE_900, color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
            on_click=lambda e: self.tela_seletor_geral(objetivo="lembrete")
        )
        
        btn_diario = ft.ElevatedButton(
            text="📝 Observações Diárias", width=280, height=42, bgcolor=ft.Colors.TEAL_700, color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
            on_click=lambda e: self.tela_seletor_geral(objetivo="diario")
        )

        self.page.add(
            badge, lbl_titulo, lbl_sub, 
            lbl_sec1, ft.Column(controls=botoes_anos, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
            lbl_sec2, ft.Column(controls=[btn_lembrete, btn_diario], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5)
        )
        self.page.update()

    def tela_seletor_geral(self, objetivo):
        self.page.controls.clear()
        titulo_texto = "📌 Escolha o Ano" if objetivo == "lembrete" else "📝 Escolha o Ano"
        lbl_titulo = ft.Text(titulo_texto, size=24, weight=ft.FontWeight.BOLD, font_family="Segoe UI", margin=ft.margin.only(top=10, bottom=20))
        
        botoes_seletor = []
        for ano in ["1º Ano", "2º Ano", "3º Ano"]:
            botoes_seletor.append(
                ft.ElevatedButton(
                    text=ano, width=280, height=48,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                    on_click=lambda e, a=ano: self.tela_turmas(a, objetivo=objetivo)
                )
            )
            
        btn_voltar = ft.TextButton(text="← Voltar", style=ft.ButtonStyle(color=ft.Colors.GREY_600), on_click=lambda e: self.tela_inicial())
        self.page.add(lbl_titulo, ft.Column(controls=botoes_seletor, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8), ft.Container(content=btn_voltar, margin=ft.margin.only(top=25)))
        self.page.update()

    def tela_turmas(self, ano_selecionado, objetivo="monitoramento"):
        self.page.controls.clear()
        self.page.floating_action_button = None
        self.baterias_animar.clear()
        self.bateria_geral_animar = None
        
        lbl_titulo = ft.Text(ano_selecionado, size=24, weight=ft.FontWeight.BOLD, font_family="Segoe UI", margin=ft.margin.only(top=10, bottom=5))
        lbl_sub = ft.Text("Escolha a turma alvo", size=13, color=ft.Colors.GREY_600, font_family="Segoe UI", margin=ft.margin.only(bottom=25))
        
        botoes_turma = []
        for turma in ["A", "B", "C", "D", "E"]:
            if objetivo == "monitoramento":
                cmd = lambda e, t=turma: self.tela_alunos(ano_selecionado, t)
            elif objetivo == "lembrete":
                cmd = lambda e, t=turma: self.tela_conteudos_bimestre(ano_selecionado, t)
            elif objetivo == "diario":
                cmd = lambda e, t=turma: self.tela_observacoes_diarias(ano_selecionado, t)
                
            botoes_turma.append(
                ft.OutlinedButton(
                    text=f"Turma {turma}", width=280, height=45,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), side={"": ft.BorderSide(1.5, ft.Colors.GREY_400)}),
                    on_click=cmd
                )
            )
            
        origem = lambda e: self.tela_inicial() if objetivo == "monitoramento" else self.tela_seletor_geral(objetivo)
        btn_voltar = ft.TextButton(text="← Voltar", style=ft.ButtonStyle(color=ft.Colors.GREY_600), on_click=origem)
        
        self.page.add(lbl_titulo, lbl_sub, ft.Column(controls=botoes_turma, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5), ft.Container(content=btn_voltar, margin=ft.margin.only(top=20)))
        self.page.update()
    def criar_canvas_bateria(self, width, height, tipo):
        canvas = ft.canvas.Canvas(width=width, height=height)
        bat_dict = {"canvas": canvas, "porcentagem": 100.0, "tipo": tipo, "w": width, "h": height}
        return canvas, bat_dict

    def tela_alunos(self, ano, turma):
        self.page.controls.clear()
        chave_turma = f"{ano}_{turma}"
        
        # BUSCA REGISTROS NO SQLITE LOCAL
        cursor = self.conexao.cursor()
        cursor.execute("SELECT idx, nome, atividades, aprendizado, frequencia, comportamento, obs FROM alunos WHERE chave_turma=?", (chave_turma,))
        linhas = cursor.fetchall()
        
        self.dados_turmas[chave_turma] = []
        if len(linhas) > 0:
            for l in linhas:
                self.dados_turmas[chave_turma].append({"nome": l[1], "atividades": l[2], "aprendizado": l[3], "frequencia": l[4], "comportamento": l[5], "obs": l[6]})
        else:
            for idx in range(1, 31):
                aluno_padrao = {"nome": f"Aluno {idx}", "atividades": "Em dia", "aprendizado": "Intermediário", "frequencia": "Frequente", "comportamento": "Comportado", "obs": ""}
                self.dados_turmas[chave_turma].append(aluno_padrao)
                cursor.execute("INSERT INTO alunos VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (chave_turma, idx, aluno_padrao["nome"], aluno_padrao["atividades"], aluno_padrao["aprendizado"], aluno_padrao["frequencia"], aluno_padrao["comportamento"], aluno_padrao["obs"]))
            self.conexao.commit()

        frame_nav = ft.Row(
            controls=[
                ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: self.tela_turmas(ano, "monitoramento")),
                ft.Text(f"{ano} • Turma {turma}", size=16, weight=ft.FontWeight.BOLD)
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=10
        )

        canvas_geral, self.bateria_geral_animar = self.criar_canvas_bateria(340, 16, "geral_mobile")
        
        frame_geral = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("MONITORAMENTO GERAL", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
                    canvas_geral
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5
            ),
            bgcolor=ft.Colors.SURFACE_VARIANT,
            padding=10,
            border_radius=12,
            margin=ft.margin.symmetric(vertical=5)
        )

        self.lista_alunos_dados.clear()
        self.baterias_animar.clear()

        lista_cards = ft.ListView(expand=True, spacing=10, padding=5)

        for i, aluno_salvo in enumerate(self.dados_turmas[chave_turma], start=1):
            canvas_aluno, bat_aluno_dict = self.criar_canvas_bateria(330, 12, "aluno_mobile")
            self.baterias_animar.append(bat_aluno_dict)

            aluno_controles = {
                "atividades": ft.Dropdown(value=aluno_salvo["atividades"], options=[ft.dropdown.Option("Em dia"), ft.dropdown.Option("Atrasadas"), ft.dropdown.Option("Incompleto")], height=45),
                "aprendizado": ft.Dropdown(value=aluno_salvo["aprendizado"], options=[ft.dropdown.Option("Forte"), ft.dropdown.Option("Intermediário"), ft.dropdown.Option("Fraco")], height=45),
                "frequencia": ft.Dropdown(value=aluno_salvo["frequencia"], options=[ft.dropdown.Option("Frequente"), ft.dropdown.Option("Intermediário"), ft.dropdown.Option("Infrequente")], height=45),
                "comportamento": ft.Dropdown(value=aluno_salvo["comportamento"], options=[ft.dropdown.Option("Comportado"), ft.dropdown.Option("Intermediário"), ft.dropdown.Option("Difícil de lidar")], height=45),
                "bat_dict": bat_aluno_dict
            }
            self.lista_alunos_dados.append(aluno_controles)

            def salvar_estado_aluno(e, posicao=i-1, ctrls=aluno_controles):
                nome_final = txt_nome.value.strip() or f"Aluno {posicao+1}"
                self.dados_turmas[chave_turma][posicao] = {
                    "nome": nome_final, "atividades": ctrls["atividades"].value,
                    "aprendizado": ctrls["aprendizado"].value, "frequencia": ctrls["frequencia"].value,
                    "comportamento": ctrls["comportamento"].value, "obs": txt_obs.value
                }
                
                db_cursor = self.conexao.cursor()
                db_cursor.execute("""
                    UPDATE alunos SET nome=?, atividades=?, aprendizado=?, frequencia=?, comportamento=?, obs=? 
                    WHERE chave_turma=? AND idx=?
                """, (nome_final, ctrls["atividades"].value, ctrls["aprendizado"].value, ctrls["frequencia"].value, ctrls["comportamento"].value, txt_obs.value, chave_turma, posicao+1))
                self.conexao.commit()
                self.atualizar_tudo()

            txt_nome = ft.TextField(value=aluno_salvo["nome"], label="Nome do Aluno", size=13, height=45, on_change=salvar_estado_aluno)
            txt_obs = ft.TextField(value=aluno_salvo["obs"], hint_text="Notas adicionais do estudante...", size=11, height=40, on_change=salvar_estado_aluno)

            aluno_controles["atividades"].on_change = salvar_estado_aluno
            aluno_controles["aprendizado"].on_change = salvar_estado_aluno
            aluno_controles["frequencia"].on_change = salvar_estado_aluno
            aluno_controles["comportamento"].on_change = salvar_estado_aluno

            card_aluno = ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            txt_nome,
                            ft.Row(controls=[ft.Text("Inad.", size=8), ft.Text("Inter.", size=8, expand=True, text_align=ft.TextAlign.CENTER), ft.Text("Adeq.", size=8)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            canvas_aluno,
                            ft.Row(controls=[aluno_controles["atividades"], aluno_controles["aprendizado"]], spacing=5, expand=True),
                            ft.Row(controls=[aluno_controles["frequencia"], aluno_controles["comportamento"]], spacing=5, expand=True),
                            txt_obs
                        ],
                        spacing=8
                    ),
                    padding=12
                )
            )
            lista_cards.controls.append(card_aluno)

        self.page.add(frame_nav, frame_geral, lista_cards)
        self.atualizar_tudo()
    def calcular_pontos(self, aluno_ctrls):
        pontos = 0
        atv = aluno_ctrls["atividades"].value
        if atv == "Em dia": pontos += 2
        elif atv == "Incompleto": pontos += 1
        
        apr = aluno_ctrls["aprendizado"].value
        if apr == "Forte": pontos += 2
        elif apr == "Intermediário": pontos += 1
        
        frq = aluno_ctrls["frequencia"].value
        if frq == "Frequente": pontos += 2
        elif frq == "Intermediário": pontos += 1
        
        cmp = aluno_ctrls["comportamento"].value
        if cmp == "Comportado": pontos += 2
        elif cmp == "Intermediário": pontos += 1
        return pontos

    def atualizar_tudo(self):
        if not self.lista_alunos_dados: return
        total_pontos_turma = 0
        max_pontos_turma = len(self.lista_alunos_dados) * 8
        
        for aluno in self.lista_alunos_dados:
            pts = self.calcular_pontos(aluno)
            total_pontos_turma += pts
            aluno["bat_dict"]["porcentagem"] = (pts / 8.0) * 100.0

        if self.bateria_geral_animar:
            self.bateria_geral_animar["porcentagem"] = (total_pontos_turma / max_pontos_turma) * 100.0
        self.page.update()

    def desenhar_bateria_onda(self, bat_dict):
        canvas = bat_dict["canvas"]
        pct = bat_dict["porcentagem"]
        tipo = bat_dict["tipo"]
        w = bat_dict["w"]
        h = bat_dict["h"]

        if pct <= 40: cor_fluido = ft.Colors.RED_ACCENT_400
        elif pct <= 75: cor_fluido = ft.Colors.ORANGE_400
        else: cor_fluido = ft.Colors.TEAL_600

        canvas.clean()
        canvas.shapes.append(ft.canvas.Rect(2, 2, w - 8, h - 4, paint=ft.Paint(style=ft.PaintingStyle.STROKE, color=ft.Colors.GREY, stroke_width=1.5), border_radius=3))
        canvas.shapes.append(ft.canvas.Rect(w - 8, 4, 5, h - 8, paint=ft.Paint(style=ft.PaintingStyle.FILL, color=ft.Colors.GREY)))

        if pct > 0:
            largura_fluido = ((pct / 100.0) * (w - 12))
            elementos_caminho = [ft.canvas.Path.MoveTo(4, h - 3)]
            for x in range(4, int(4 + largura_fluido)):
                y = (h / 2) + math.sin((x / 8) + self.fase_onda) * 1.8
                y_fixo = max(2, min(h - 3, int(y - ((100 - pct) / 100) * 1.5)))
                elementos_caminho.append(ft.canvas.Path.LineTo(x, y_fixo))
                
            elementos_caminho.append(ft.canvas.Path.LineTo(4 + largura_fluido, h - 3))
            elementos_caminho.append(ft.canvas.Path.Close())
            canvas.shapes.append(ft.canvas.Path(elementos_caminho, paint=ft.Paint(style=ft.PaintingStyle.FILL, color=cor_fluido)))
        canvas.update()

    def loop_animacao_ondas(self):
        while self.animacao_ativa:
            self.fase_onda += 0.25
            for bat in list(self.baterias_animar):
                try: self.desenhar_bateria_onda(bat)
                except: pass
            if self.bateria_geral_animar:
                try: self.desenhar_bateria_onda(self.bateria_geral_animar)
                except: pass
            time.sleep(0.05)
    def tela_conteudos_bimestre(self, ano, turma):
        self.page.controls.clear()
        frame_nav = ft.Row(controls=[ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: self.tela_turmas(ano, "lembrete")), ft.Text(f"Conteúdos: {ano} • Turma {turma}", size=16, weight=ft.FontWeight.BOLD)])
        lista_conteudos = ft.ListView(expand=True, spacing=10)
        for b in range(1, 5):
            card_b = ft.Card(content=ft.Container(content=ft.Column(controls=[ft.Text(f"📌 {b}º BIMESTRE", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800), ft.TextField(label="Resumo do Conteúdo Programático", multiline=True, min_lines=3, max_lines=5, hint_text=f"Digite o resumo no {b}º Bimestre aqui...")]), padding=12))
            lista_conteudos.controls.append(card_b)
        self.page.add(frame_nav, lista_conteudos)
        self.page.update()

    def tela_observacoes_diarias(self, ano, turma):
        self.page.controls.clear()
        chave_turma = f"{ano}_{turma}"
        
        if chave_turma not in self.dados_turmas:
            cursor_db = self.conexao.cursor()
            cursor_db.execute("SELECT nome FROM alunos WHERE chave_turma=?", (chave_turma,))
            linhas_al = cursor_db.fetchall()
            self.dados_turmas[chave_turma] = [{"nome": r[0]} for r in linhas_al] if len(linhas_al) > 0 else [{"nome": f"Aluno {idx}"} for idx in range(1, 31)]

        frame_nav = ft.Row(controls=[ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: self.tela_turmas(ano, "diario")), ft.Text(f"Diário: {ano} • Turma {turma}", size=16, weight=ft.FontWeight.BOLD)])
        container_lista = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)

        def renderizar_historico():
            container_lista.controls.clear()
            
            cursor = self.conexao.cursor()
            cursor.execute("SELECT id, data, atividade, pagina, participantes FROM historico WHERE chave_turma=? ORDER BY id DESC", (chave_turma,))
            registros = cursor.fetchall()
            
            self.historico_diario[chave_turma] = []
            for r in registros:
                self.historico_diario[chave_turma].append({"id_db": r[0], "data": r[1], "atividade": r[2], "pagina": r[3], "participantes": r[4]})
                
            if not self.historico_diario[chave_turma]:
                container_lista.controls.append(ft.Container(content=ft.Text("Nenhuma nota registrada.\nClique no botão [+] abaixo para adicionar.", size=13, italic=True, text_align=ft.TextAlign.CENTER), alignment=ft.alignment.center, padding=40))
                self.page.update()
                return

            for idx_nota, nota in enumerate(self.historico_diario[chave_turma]):
                def excluir_nota(e, id_registro=nota["id_db"]):
                    cursor_del = self.conexao.cursor()
                    cursor_del.execute("DELETE FROM historico WHERE id=?", (id_registro,))
                    self.conexao.commit()
                    renderizar_historico()

                card_salvo = ft.Card(content=ft.Container(content=ft.Column(controls=[ft.Text(f"📅 Atividades no dia {nota['data']}", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700), ft.Text(f"• Tipo: {nota['atividade']}\n• Página: {nota['pagina'] or 'N/A'}\n• Participantes: {nota['participantes']}", size=11), ft.Row(controls=[ft.TextButton("✏️ Editar", on_click=lambda e, i=idx_nota: abrir_formulario_cadastro(indice_edicao=i)), ft.TextButton("🗑️ Excluir", style=ft.ButtonStyle(color=ft.Colors.RED_600), on_click=excluir_nota)], alignment=ft.MainAxisAlignment.END)]), padding=12))
                container_lista.controls.append(card_salvo)
            self.page.update()

        def abrir_formulario_cadastro(indice_edicao=None):
            dados = self.historico_diario[chave_turma][indice_edicao] if indice_edicao is not None else None
            
            txt_data = ft.TextField(label="Data (DD/MM/AAAA)", value=dados["data"] if dados else "", hint_text="Ex: 27/06/2026", size=13)
            txt_pagina = ft.TextField(label="📖 QUAL A PÁGINA?", value=dados["pagina"] if dados else "", hint_text="Nº da página...", size=13, visible=False)
            txt_listagem = ft.TextField(label="Alunos Confirmados", value=dados["participantes"] if dados else "Alunos confirmados: ", multiline=True, min_lines=2, max_lines=4, size=11, read_only=True)

            def formatar_data(e):
                texto = "".join([c for c in txt_data.value if c.isdigit()])[:8]
                if len(texto) >= 5: txt_data.value = f"{texto[:2]}/{texto[2:4]}/{texto[4:]}"
                elif len(texto) >= 3: txt_data.value = f"{texto[:2]}/{texto[2:]}"
                else: txt_data.value = texto
                txt_data.update()

            txt_data.on_change = formatar_data

            def checar_atividade_livro(e):
                txt_pagina.visible = (cb_atv_hoje.value == "Atividade do Livro")
                txt_pagina.update()

            cb_atv_hoje = ft.Dropdown(label="Atividade", value=dados["atividade"] if dados else "Aula Prática", options=[ft.dropdown.Option("Aula Prática"), ft.dropdown.Option("Atividade do Livro"), ft.dropdown.Option("Atividade no Quadro"), ft.dropdown.Option("Trabalho")], on_change=checar_atividade_livro)
            if dados and dados["atividade"] == "Atividade do Livro": txt_pagina.visible = True

            alunos_lista = [self.dados_turmas[chave_turma][n]["nome"] for n in range(len(self.dados_turmas[chave_turma]))]
            
            def adicionar_aluno_pauta(e):
                if cb_participantes.value and cb_participantes.value not in txt_listagem.value:
                    prefixo = "" if txt_listagem.value.strip() == "Alunos confirmados:" else ", "
                    txt_listagem.value += f"{prefixo}{cb_participantes.value}"
                    txt_listagem.update()

            cb_participantes = ft.Dropdown(label="👥 ALUNOS QUE PARTICIPARAM", options=[ft.dropdown.Option(a) for a in alunos_lista], height=48, on_change=adicionar_aluno_pauta)

            def salvar_nota(e):
                if not txt_data.value: return
                pauta_limpa = txt_listagem.value.replace("Alunos confirmados:", "").strip()
                
                cursor_save = self.conexao.cursor()
                if indice_edicao is not None:
                    cursor_save.execute("""
                        UPDATE historico SET data=?, atividade=?, pagina=?, participantes=? WHERE id=?
                    """, (txt_data.value, cb_atv_hoje.value, txt_pagina.value, pauta_limpa, dados["id_db"]))
                else:
                    cursor_save.execute("""
                        INSERT INTO historico (chave_turma, data, atividade, pagina, participantes) VALUES (?, ?, ?, ?, ?)
                    """, (chave_turma, txt_data.value, cb_atv_hoje.value, txt_pagina.value, pauta_limpa))
                
                self.conexao.commit()
                self.page.dialog.open = False
                renderizar_historico()

            self.page.dialog = ft.AlertDialog(
                title=ft.Text("REGISTRAR ATIVIDADE", size=14, weight=ft.FontWeight.BOLD),
                content=ft.Container(content=ft.Column(controls=[cb_atv_hoje, txt_pagina, cb_participantes, txt_listagem, txt_data], spacing=10, tight=True), width=340),
                actions=[
                    ft.TextButton("✕ Fechar Aba", style=ft.ButtonStyle(color=ft.Colors.RED_600), on_click=lambda e: setattr(self.page.dialog, "open", False) or self.page.update()),
                    ft.ElevatedButton("💾 Salvar Nota", bgcolor=ft.Colors.TEAL_700, color=ft.Colors.WHITE, on_click=salvar_nota)
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            self.page.dialog.open = True
            self.page.update()

        self.page.floating_action_button = ft.FloatingActionButton(icon=ft.Icons.ADD, bgcolor=ft.Colors.TEAL_700, color=ft.Colors.WHITE, on_click=lambda e: abrir_formulario_cadastro())
        self.page.add(frame_nav, container_lista)
        renderizar_historico()

def main(page: ft.Page):
    MonitoramentoAppMobile(page)

if __name__ == "__main__":
    ft.app(target=main)
