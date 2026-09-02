export interface AdminUsuario {
  id: number;
  nome: string;
  email: string;
  role: string;
  criado_em: string;
}

export interface AdminComentario {
  id: number;
  tmdb_movie_id: number;
  titulo: string | null;
  poster_path: string | null;
  nome_usuario: string | null;
  texto: string;
  criado_em: string;
  meu: boolean;
}

export interface AdminFavorito {
  id: number;
  tmdb_movie_id: number;
  titulo: string;
  poster_path: string | null;
  criado_em: string;
  usuario_id: number;
}
