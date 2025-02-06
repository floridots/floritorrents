import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import List, Optional
import re
from urllib.parse import quote
import traceback
from datetime import datetime
import time
from PIL import Image, ImageTk
from io import BytesIO

@dataclass
class TorrentResult:
    name: str
    size: int
    seeders: int
    leechers: int
    magnet: str
    source: str
    has_pt_subs: bool = False  # Novo campo para legendas em português

@dataclass
class TorrentDetails:
    season: Optional[int] = None
    episode: Optional[int] = None
    quality: str = ''
    quality_rank: int = 0
    has_pt_subs: bool = False
    
    @staticmethod
    def parse_title(title: str) -> 'TorrentDetails':
        details = TorrentDetails()
        
        # Padrões para detecção de legendas em português
        pt_sub_patterns = [
            r'\b(?:por|pt|br|pt-br|por-pt)\b',
            r'\b(?:multi[\s-]*sub|multi[\s-]*subs|multiple[\s-]*subtitles?)\b',
            r'legendas?[\s-]*(?:pt|por|br)',
            r'dual[\s-]*audio',
            r'dubbed',
            r'\[pt\]|\(pt\)|\[br\]|\(br\)',
            r'\bleg\b'
        ]
        
        lower_title = title.lower()
        for pattern in pt_sub_patterns:
            if re.search(pattern, lower_title):
                details.has_pt_subs = True
                break
        
        season_ep = re.search(r'[Ss](\d{1,2})[Ee](\d{1,2})|(\d{1,2})x(\d{1,2})', title)
        if season_ep:
            if season_ep.group(1) and season_ep.group(2):
                details.season = int(season_ep.group(1))
                details.episode = int(season_ep.group(2))
            elif season_ep.group(3) and season_ep.group(4):
                details.season = int(season_ep.group(3))
                details.episode = int(season_ep.group(4))
        
        quality_patterns = [
            (r'2160p|4K', '2160p', 4),
            (r'1080p', '1080p', 3),
            (r'720p', '720p', 2),
            (r'480p', '480p', 1),
            (r'HDRip|WEB-DL|BRRip|BluRay', 'HD', 2)
        ]
        
        for pattern, quality, rank in quality_patterns:
            if re.search(pattern, title, re.IGNORECASE):
                details.quality = quality
                details.quality_rank = rank
                break
        
        return details

class MediaSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FloriMovies Torrent")
        self.root.geometry("1200x700")
        self.root.configure(background="#f0f0f0")
        
        # Configuração para que a janela seja responsiva
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        self.api_key = "ab3e577cc4cbe71da18c73b74f748be1"
        self.user_agent = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/120.0.0.0 Safari/537.36")
        self.jackett_api_key = "i17t71clvbcm7ap8sgldk3r37zko5cl1"
        self.jackett_host = "http://localhost:9117"
        self.tmdb_image_base_url = "https://image.tmdb.org/t/p/w200"  # URL base para imagens TMDb
        
        self.create_widgets()
        self.configure_styles()

    def configure_styles(self):
        # Utiliza o tema 'clam' para um visual mais limpo
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", font=('Arial', 10))
        style.configure("TButton", font=('Arial', 10, 'bold'),
                        background="#4CAF50", foreground="white", padding=6)
        style.map("TButton", background=[('active', '#45A049')])
        style.configure("Hover.TButton", font=('Arial', 10, 'bold'),
                        background="#45A049", foreground="white", padding=6)
        style.configure("Treeview", font=('Arial', 10), rowheight=25)
        style.configure("TEntry", font=('Arial', 10))
        # Novos estilos para header e detalhes
        style.configure("Header.TLabel", font=('Arial', 20, 'bold'),
                        background="#f0f0f0", foreground="#333")
        style.configure("Details.TLabel", font=('Arial', 11),
                        background="#f0f0f0", foreground="#333")
        
    def create_widgets(self):
        # Cabeçalho moderno com novo estilo
        header = ttk.Label(self.root, text="FloriMovies Torrent", style="Header.TLabel")
        header.pack(pady=(10,5))
        
        control_frame = ttk.Frame(self.root)
        control_frame.pack(pady=10, padx=10, fill='x')

        entries = [
            ('Nome:', 'name_entry', 25),
            ('Ano:', 'year_entry', 7),
            ('Avaliação Mínima:', 'rating_entry', 5)
        ]

        for col, (text, var, width) in enumerate(entries):
            ttk.Label(control_frame, text=text).grid(row=0, column=col*2, padx=5, pady=5)
            entry = ttk.Entry(control_frame, width=width, style="TEntry")
            entry.grid(row=0, column=col*2+1, padx=5, pady=5)
            setattr(self, var, entry)

        self.type_var = tk.StringVar()
        ttk.Label(control_frame, text="Tipo:").grid(row=0, column=6, padx=5, pady=5)
        type_combo = ttk.Combobox(
            control_frame,
            textvariable=self.type_var,
            values=["Todos", "Filmes", "Séries", "Anime"],
            width=8,
            state="readonly"
        )
        type_combo.grid(row=0, column=7, padx=5, pady=5)
        self.type_var.set("Todos")

        # Botão com efeito hover
        search_button = ttk.Button(control_frame, text="Buscar", command=self.search_media, style="TButton")
        search_button.grid(row=0, column=8, padx=5, pady=5)
        search_button.bind('<Enter>', lambda e: search_button.configure(style="Hover.TButton"))
        search_button.bind('<Leave>', lambda e: search_button.configure(style="TButton"))

        # Treeview principal para resultados
        self.tree = ttk.Treeview(
            self.root,
            columns=('Title', 'Year', 'Type', 'Rating'),
            show='headings',
            selectmode='browse',
            style="Custom.Treeview"
        )

        # Frame para detalhes do item selecionado
        self.details_frame = ttk.Frame(self.root)
        self.details_frame.pack(side='right', fill='y', padx=10, pady=10)

        # Label para a imagem (cover)
        self.poster_label = ttk.Label(self.details_frame)
        self.poster_label.pack(pady=10)

        # Label para informações adicionais
        self.info_label = ttk.Label(
            self.details_frame,
            text="Selecione um item para ver detalhes",
            wraplength=300,  # aumentei o wraplength para melhor visualização
            justify='left',
            style="Details.TLabel"
        )
        self.info_label.pack(pady=5)

        # Novo widget ScrolledText para exibir a sinopse com scroll
        self.sinopse_text = scrolledtext.ScrolledText(
            self.details_frame,
            wrap='word',
            width=40,
            height=10,
            font=('Arial', 10),
            background="#f0f0f0",
            foreground="#333"
        )
        self.sinopse_text.pack(pady=5)
        self.sinopse_text.configure(state='disabled')

        # Bind para seleção na tree
        self.tree.bind('<<TreeviewSelect>>', self.show_selected_details)

        col_configs = [
            ('Title', 400),
            ('Year', 80),
            ('Type', 100),
            ('Rating', 80)
        ]
        for col, (text, width) in zip(self.tree['columns'], col_configs):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor='center')

        scrollbar = ttk.Scrollbar(self.root, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(fill='both', expand=True, padx=10, pady=5)
        scrollbar.pack(side='right', fill='y')
        self.tree.bind('<Double-1>', self.show_torrents)

        # Área de log com visual clean
        self.log_text = tk.Text(self.root, height=8, state='disabled',
                                font=('Arial', 10), background="#ffffff")
        self.log_text.pack(fill='x', padx=10, pady=5)

    def fade_in(self, window, delay=10, step=0.05):
        """Animação de fade in para uma janela."""
        alpha = window.attributes('-alpha')
        if alpha < 1:
            alpha += step
            window.attributes('-alpha', alpha)
            window.after(delay, lambda: self.fade_in(window, delay, step))
        else:
            window.attributes('-alpha', 1)

    def log(self, message: str):
        self.log_text.configure(state='normal')
        self.log_text.insert('end', message + '\n')
        self.log_text.configure(state='disabled')
        self.log_text.see('end')

    def search_media(self):
        self.tree.delete(*self.tree.get_children())
        self.log("Iniciando busca...")
        
        try:
            params = self.validate_inputs()
        except ValueError as e:
            messagebox.showerror("Erro", str(e))
            return

        results = []
        selected_type = self.type_var.get()
        
        # Busca em TMDb (para filmes e séries)
        if selected_type in ["Todos", "Filmes", "Séries"]:
            media_types = []
            if selected_type in ["Todos", "Filmes"]:
                media_types.append('movie')
            if selected_type in ["Todos", "Séries"]:
                media_types.append('tv')
                
            for media_type in media_types:
                self.log(f"Buscando em TMDb: {media_type}...")
                results.extend(self.fetch_tmdb_data(media_type, params))

        # Busca em Jikan/MyAnimeList
        if selected_type in ["Todos", "Anime"]:
            self.log("Buscando em MyAnimeList...")
            results.extend(self.fetch_jikan_data(params))

        self.update_tree_with_results(results)
        self.log(f"Busca concluída. {len(results)} resultados encontrados.")

    def fetch_jikan_data(self, params: dict) -> List[dict]:
        results = []
        try:
            base_url = "https://api.jikan.moe/v4/anime"
            query_params = {}
            
            if params['name']:
                query_params['q'] = params['name']
            if params['year']:
                query_params['start_date'] = f"{params['year']}-01-01"
                query_params['end_date'] = f"{params['year']}-12-31"
            if params['rating']:
                query_params['min_score'] = params['rating']
            
            self.log("Fazendo requisição para Jikan API...")
            response = requests.get(
                base_url,
                params=query_params,
                headers={'User-Agent': self.user_agent}
            )
            response.raise_for_status()
            data = response.json()
            time.sleep(1)
            
            for item in data.get('data', []):
                year = 'N/A'
                if item.get('aired', {}).get('from'):
                    year = item['aired']['from'][:4]
                
                result = {
                    'title': item.get('title'),
                    'year': year,
                    'type': 'Anime',
                    'rating': round(float(item.get('score', 0)), 1),
                    'poster_path': item.get('images', {}).get('jpg', {}).get('image_url'),
                    'sinopse': item.get('synopsis', 'Sinopse não disponível')  # Nova linha para sinopse
                }
                
                if (not params['rating'] or result['rating'] >= params['rating']) and \
                   (not params['year'] or str(params['year']) == str(year)):
                    # Gerar ID único para o item
                    item_id = f"jikan_{item.get('mal_id')}"
                    self.media_items[item_id] = result
                    results.append((item_id, result))
            
            self.log(f"Encontrados {len(results)} animes.")
            
        except requests.exceptions.RequestException as e:
            self.log(f"Erro na requisição ao Jikan: {e}")
        except Exception as e:
            self.log(f"Erro ao processar dados do Jikan: {e}")
        
        return results

    def validate_inputs(self) -> dict:
        params = {
            'name': self.name_entry.get().strip(),
            'year': None,
            'rating': 0.0
        }

        if self.year_entry.get().strip():
            year = int(self.year_entry.get())
            if not (1888 < year < 2100):
                raise ValueError("Ano deve ser entre 1889-2099")
            params['year'] = year

        if self.rating_entry.get().strip():
            rating = float(self.rating_entry.get())
            if not (0 <= rating <= 10):
                raise ValueError("Avaliação deve ser entre 0-10")
            params['rating'] = rating

        return params

    def fetch_tmdb_data(self, media_type: str, params: dict) -> List[dict]:
        results = []
        if not hasattr(self, 'media_items'):
            self.media_items = {}
        
        try:
            page = 1
            while True:
                url, query_params = self.build_tmdb_query(media_type, params, page)
                response = requests.get(url, params=query_params)
                response.raise_for_status()
                data = response.json()

                for item in data.get('results', []):
                    processed = self.process_tmdb_item(item, media_type, params)
                    if processed:
                        # Adicionar poster_path aos dados processados
                        processed['poster_path'] = item.get('poster_path')
                        
                        # Gerar ID único para o item
                        item_id = f"tmdb_{item.get('id')}"
                        self.media_items[item_id] = processed
                        
                        results.append((item_id, processed))

                if page >= data.get('total_pages', 1):
                    break
                page += 1

        except requests.exceptions.RequestException as e:
            self.log(f"Erro na requisição ao TMDb: {e}")
            return []

        return results

    def build_tmdb_query(self, media_type: str, params: dict, page: int):
        if params['name']:
            url = f'https://api.themoviedb.org/3/search/{media_type}'
            query_params = {
                'api_key': self.api_key,
                'query': params['name'],
                'page': page,
                'include_adult': 'false',
                'language': 'en-US'
            }
            year_param = 'primary_release_year' if media_type == 'movie' else 'first_air_date_year'
            if params['year']:
                query_params[year_param] = params['year']
        else:
            url = f'https://api.themoviedb.org/3/discover/{media_type}'
            query_params = {
                'api_key': self.api_key,
                'vote_average.gte': params['rating'],
                'sort_by': 'vote_average.desc',
                'vote_count.gte': 500,
                'page': page,
                'language': 'en-US'
            }
            if params['year']:
                year_param = 'primary_release_year' if media_type == 'movie' else 'first_air_date_year'
                query_params[year_param] = params['year']

        return url, query_params

    def process_tmdb_item(self, item: dict, media_type: str, params: dict) -> Optional[dict]:
        title = item.get('title') if media_type == 'movie' else item.get('name')
        date = item.get('release_date') if media_type == 'movie' else item.get('first_air_date')
        vote_count = item.get('vote_count', 0)
        rating = round(item.get('vote_average', 0), 1)

        if params['name'] and (rating < params['rating'] or vote_count < 500):
            return None

        return {
            'title': title,
            'year': date[:4] if date else 'N/A',
            'type': 'Movie' if media_type == 'movie' else 'TV Series',
            'rating': rating,
            'sinopse': item.get('overview', 'Synopsis not available')
        }

    def show_selected_details(self, event):
        """Mostra os detalhes do item selecionado, incluindo a imagem e agora a sinopse"""
        selected = self.tree.selection()
        if not selected:
            return

        item_id = selected[0]
        if hasattr(self, 'media_items') and item_id in self.media_items:
            media_item = self.media_items[item_id]
            
            # Carregar e exibir a imagem
            if media_item.get('poster_path'):
                self.load_and_display_image(media_item['poster_path'])
            
            # Atualizar informações
            info_text = f"""
Título: {media_item.get('title', '')}
Ano: {media_item.get('year', '')}
Avaliação: {media_item.get('rating', '')}
Tipo: {media_item.get('type', '')}
"""
            self.info_label.configure(text=info_text)
            
            # Atualizar a sinopse no novo widget com tradução para animes
            sinopse = media_item.get('sinopse', 'Sinopse não disponível')
            if media_item.get('type', '').lower() == 'anime':
                sinopse = self.translate_to_portuguese(sinopse)
            self.sinopse_text.configure(state='normal')
            self.sinopse_text.delete(1.0, tk.END)
            self.sinopse_text.insert(tk.END, sinopse)
            self.sinopse_text.configure(state='disabled')

    def load_and_display_image(self, image_path):
        """Carrega e exibe a imagem do poster"""
        try:
            # Determinar URL da imagem baseado no tipo (TMDb ou MyAnimeList)
            if image_path.startswith('http'):
                image_url = image_path
            else:
                image_url = f"{self.tmdb_image_base_url}{image_path}"

            response = requests.get(image_url)
            image = Image.open(BytesIO(response.content))
            
            # Redimensionar mantendo proporção
            basewidth = 200
            wpercent = (basewidth/float(image.size[0]))
            hsize = int((float(image.size[1])*float(wpercent)))
            image = image.resize((basewidth, hsize), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(image)
            self.poster_label.configure(image=photo)
            self.poster_label.image = photo  # Manter referência
        except Exception as e:
            self.log(f"Erro ao carregar imagem: {e}")
            self.poster_label.configure(image='')

    def update_tree_with_results(self, results):
        self.tree.delete(*self.tree.get_children())
        if not results:
            messagebox.showinfo("Sem resultados", "Nenhum resultado encontrado!")
            return

        for item_id, item in sorted(results, key=lambda x: x[1]['rating'], reverse=True):
            self.tree.insert('', 'end', item_id, values=(
                item['title'],
                item['year'],
                item['type'],
                item['rating']
            ))

    def show_torrents(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        item = self.tree.item(selected[0], 'values')
        title = item[0]
        media_type = item[2]

        search_title = title
        if media_type == "Anime":
            search_title = re.sub(r'\([^)]*\)', '', title)
            search_title = re.sub(r': .*$', '', search_title)
            search_title = search_title.strip()

        # Cria uma nova janela para os torrents com fade in
        self.torrent_window = tk.Toplevel(self.root)
        self.torrent_window.title(f"Torrents: {title}")
        self.torrent_window.geometry("1200x600")
        self.torrent_window.configure(background="#f0f0f0")
        self.torrent_window.attributes("-alpha", 0.0)
        self.fade_in(self.torrent_window)

        style = ttk.Style()
        style.configure("Treeview", rowheight=25)

        columns = ('Name', 'Size', 'Seeders', 'Leechers', 'Source', 'Season', 'Quality', 'Subs')
        self.torrent_tree = ttk.Treeview(self.torrent_window, columns=columns, show='headings', style="Treeview")
        
        widths = {
            'Name': 400,
            'Size': 100,
            'Seeders': 80,
            'Leechers': 80,
            'Source': 150,
            'Season': 100,
            'Quality': 100,
            'Subs': 80
        }
        
        for col in columns:
            self.torrent_tree.heading(col, text=col)
            self.torrent_tree.column(col, width=widths[col], anchor='center')
        self.torrent_tree.column('Name', anchor='w')
        
        scrollbar = ttk.Scrollbar(self.torrent_window, orient='vertical', command=self.torrent_tree.yview)
        self.torrent_tree.configure(yscrollcommand=scrollbar.set)
        
        self.torrent_tree.pack(fill='both', expand=True, padx=10, pady=10)
        scrollbar.pack(side='right', fill='y')
        
        self.torrent_tree.bind('<Double-1>', self.copy_magnet)

        Thread(target=self.fetch_torrents, args=(search_title, media_type), daemon=True).start()

    def fetch_torrents(self, title: str, media_type: str):
        self.log(f"\n{'='*50}")
        self.log(f"INICIANDO BUSCA DE TORRENTS PARA: {title}")
        self.log(f"Tipo de mídia: {media_type}")
        
        try:
            results = []
            year_match = re.search(r'\((\d{4})\)$', title)
            if year_match:
                year = year_match.group(1)
                base_title = title.split(' (')[0]
                query = f"{base_title} {year}"
            else:
                query = title
            
            with ThreadPoolExecutor(max_workers=2) as executor:
                self.log("\nIniciando busca paralela:")
                self.log("Submetendo busca ao Apibay...")
                future_apibay = executor.submit(self.search_apibay, query, '200' if media_type == 'Filme' else '500')
                self.log("Submetendo busca ao Jackett...")
                future_jackett = executor.submit(self.search_jackett, query)
                self.log("\nAguardando resultados...")
                for future in [future_apibay, future_jackett]:
                    try:
                        service_name = "Apibay" if future == future_apibay else "Jackett"
                        result = future.result(timeout=25)
                        self.log(f"\nResultados de {service_name}:")
                        self.log(f"Total encontrado: {len(result)}")
                        if result:
                            self.log(f"Exemplo: {result[0].name[:50]}...")
                        results += result
                    except Exception as e:
                        self.log(f"\nERRO EM {service_name}:")
                        self.log(traceback.format_exc())
                        continue

            processed = self.process_results(results, title)
            self.current_torrents = processed  # Armazena os resultados atuais
            self.log(f"\nResultados finais após processamento:")
            self.log(f"Total: {len(processed)}")
            self.log(f"Fontes: {list(set(r.source for r in processed))}")
            self.root.after(0, self.update_torrent_tree, processed)

        except Exception as e:
            self.log(f"\nERRO GRAVE NA BUSCA:")
            self.log(traceback.format_exc())
            self.root.after(0, self.show_error, f"Erro fatal: {str(e)}")

    def search_apibay(self, query: str, category: str) -> List[TorrentResult]:
        try:
            response = requests.get(
                f"https://apibay.org/q.php?q={query}&cat={category}",
                headers={'User-Agent': self.user_agent},
                timeout=10
            )
            return [
                TorrentResult(
                    name=t['name'],
                    size=int(t['size']),
                    seeders=int(t['seeders']),
                    leechers=int(t['leechers']),
                    magnet=f"magnet:?xt=urn:btih:{t['info_hash']}",
                    source='Apibay'
                ) for t in response.json() if t['name'] != 'No results returned'
            ]
        except Exception as e:
            self.log(f"Erro no Apibay: {e}")
            return []

    def search_jackett(self, query: str) -> List[TorrentResult]:
        try:
            self.log(f"\n=== INICIANDO BUSCA NO JACKETT ===")
            self.log(f"Horário: {datetime.now().strftime('%H:%M:%S.%f')}")
            self.log(f"Parâmetro recebido - Query: {query}")            
            self.log(f"\nConfiguração do Jackett:")
            self.log(f"Host: {self.jackett_host}")
            self.log(f"API Key: {'***' + self.jackett_api_key[-3:] if self.jackett_api_key else 'Nenhuma'}")
            
            url = f"{self.jackett_host}/api/v2.0/indexers/all/results"
            decoded_query = query.replace('%20', ' ')
            params = {
                'apikey': self.jackett_api_key,
                'Query': decoded_query,
            }
            self.log(f"\nConstruindo requisição:")
            self.log(f"URL: {url}")
            self.log(f"Parâmetros: {params}")
            self.log(f"\nEnviando requisição para o Jackett...")
            start_time = datetime.now()
            response = requests.get(
                url,
                params=params,
                headers={'User-Agent': self.user_agent},
                timeout=15
            )
            latency = (datetime.now() - start_time).total_seconds()
            self.log(f"\nResposta recebida:")
            self.log(f"Status Code: {response.status_code}")
            self.log(f"Latência: {latency:.2f}s")
            self.log(f"URL final: {response.url}")
            self.log(f"Cabeçalhos: {dict(response.headers)}")
            if response.status_code != 200:
                self.log(f"\nERRO NA RESPOSTA:")
                self.log(f"Conteúdo da resposta: {response.text[:500]}...")
                response.raise_for_status()
            
            data = response.json()
            self.log(f"Estrutura do JSON recebido: {list(data.keys())}")
            self.log(f"Número de resultados: {len(data.get('Results', []))}")
            results = []
            for item in data.get('Results', []):
                magnet = item['MagnetUri'] or f"magnet:?xt=urn:btih:{item['InfoHash']}"
                magnet = requests.utils.requote_uri(magnet)
                result = TorrentResult(
                    name=item['Title'],
                    size=item['Size'],
                    seeders=item['Seeders'],
                    leechers=item['Peers'] - item['Seeders'],
                    magnet=magnet,
                    source=f"Jackett/{item['Tracker']}"
                )
                results.append(result)
            self.log(f"\nBusca no Jackett concluída. {len(results)} resultados válidos.")
            return results

        except Exception as e:
            self.log(f"\nERRO INESPERADO NO JACKETT:")
            self.log(traceback.format_exc())
            return []
        
    def process_results(self, results: List[TorrentResult], title: str) -> List[TorrentResult]:
        processed_results = []
        seen = set()
        for item in results:
            if (item.name, item.size) not in seen and item.seeders > 0:
                seen.add((item.name, item.size))
                details = TorrentDetails.parse_title(item.name)
                processed_results.append((item, details))
        sorted_results = sorted(
            processed_results,
            key=lambda x: (
                x[1].season or float('inf'),
                x[1].episode or float('inf'),
                -x[1].quality_rank,
                -x[0].seeders
            )
        )
        return [item[0] for item in sorted_results]

    def update_torrent_tree(self, data: List[TorrentResult]):
        self.torrent_tree.delete(*self.torrent_tree.get_children())
        if not data:
            messagebox.showinfo("Info", "Nenhum torrent encontrado!")
            return
        for item in data:
            details = TorrentDetails.parse_title(item.name)
            season_ep = ''
            if details.season is not None and details.episode is not None:
                season_ep = f'S{details.season:02d}E{details.episode:02d}'
            quality = details.quality or 'N/A'
            flag = "🇧🇷" if details.has_pt_subs else ""
            self.torrent_tree.insert('', 'end', values=(
                item.name,
                self.convert_size(item.size),
                item.seeders,
                item.leechers,
                item.source,
                season_ep,
                quality,
                flag
            ))

    def convert_size(self, size_bytes: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return "N/A"

    def copy_magnet(self, event):
        selected = self.torrent_tree.selection()
        if not selected:
            return
        try:
            item_values = self.torrent_tree.item(selected[0])["values"]
            selected_name = item_values[0]
            magnet_link = None
            for result in self.current_torrents:
                if result.name == selected_name:
                    magnet_link = result.magnet
                    break
            if not magnet_link or magnet_link == "magnet:?xt=urn:btih:None" or "xt=urn:btih:" not in magnet_link:
                messagebox.showerror("Erro", "Link magnet inválido ou não disponível para este torrent!")
                return
            import os
            if os.name == 'nt':
                os.startfile(magnet_link)
            else:
                import subprocess
                subprocess.run(['xdg-open', magnet_link], check=True)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir o link: {str(e)}")
            self.log(f"Erro ao abrir magnet: {traceback.format_exc()}")

    def show_error(self, message: str):
        messagebox.showerror("Erro", message)

    def translate_to_portuguese(self, text: str) -> str:
        try:
            from googletrans import Translator
            translator = Translator()
            translated = translator.translate(text, dest='pt')
            return translated.text
        except Exception as e:
            self.log(f"Falha ao traduzir: {e}")
            return text

if __name__ == "__main__":
    root = tk.Tk()
    app = MediaSearchApp(root)
    root.mainloop()