import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { FavoritesService } from '../../core/services/favorites.service';
import { MoviesService } from '../../core/services/movies.service';
import { Favorite } from '../../models/favorite.model';
import { Movie } from '../../models/movie.model';
import { MovieCard } from '../../shared/movie-card/movie-card';

@Component({
  selector: 'app-catalog',
  standalone: true,
  imports: [CommonModule, FormsModule, MovieCard],
  templateUrl: './catalog.html',
  styleUrl: './catalog.css',
})
export class Catalog implements OnInit, OnDestroy {
  filmes = signal<Movie[]>([]);
  favoritos = signal<Favorite[]>([]);
  carregando = signal(true);
  erro = signal('');

  busca = signal('');
  private buscaTimeout?: ReturnType<typeof setTimeout>;

  pagina = signal(1);
  totalPaginas = signal(1);
  paginas = computed(() => Array.from({ length: this.totalPaginas() }, (_, i) => i + 1));

  constructor(
    private readonly moviesService: MoviesService,
    private readonly favoritesService: FavoritesService,
  ) {}

  ngOnInit(): void {
    this.carregarFavoritos();
    this.carregarFilmes();
  }

  ngOnDestroy(): void {
    clearTimeout(this.buscaTimeout);
  }

  onBuscaChange(valor: string): void {
    this.busca.set(valor);
    clearTimeout(this.buscaTimeout);
    this.buscaTimeout = setTimeout(() => {
      this.pagina.set(1);
      this.carregarFilmes();
    }, 350);
  }

  private carregarFilmes(): void {
    this.carregando.set(true);
    this.moviesService.listar(this.pagina(), this.busca()).subscribe({
      next: (resposta) => {
        this.filmes.set(resposta.itens);
        this.totalPaginas.set(resposta.total_paginas);
        this.carregando.set(false);
      },
      error: () => {
        this.erro.set('Não foi possível carregar os filmes.');
        this.carregando.set(false);
      },
    });
  }

  private carregarFavoritos(): void {
    this.favoritesService.listar().subscribe({
      next: (favoritos) => this.favoritos.set(favoritos),
    });
  }

  irParaPagina(pagina: number): void {
    if (pagina < 1 || pagina > this.totalPaginas() || pagina === this.pagina()) {
      return;
    }
    this.pagina.set(pagina);
    this.carregarFilmes();
  }

  favoritoDoFilme(tmdbMovieId: number): Favorite | undefined {
    return this.favoritos().find((f) => f.tmdb_movie_id === tmdbMovieId);
  }

  posterPath(filme: Movie): string | null {
    return filme.poster_url ? filme.poster_url.replace(/^.*\/t\/p\/w500/, '') : null;
  }

  alternarFavorito(filme: Movie): void {
    const favoritoExistente = this.favoritoDoFilme(filme.tmdb_movie_id);

    if (favoritoExistente) {
      // Atualização otimista: reflete na hora, sem esperar um novo GET /favorites.
      this.favoritos.update((atual) => atual.filter((f) => f.id !== favoritoExistente.id));
      this.favoritesService.remover(favoritoExistente.id).subscribe({
        error: () => this.carregarFavoritos(), // reverte pro estado real se falhar
      });
      return;
    }

    this.favoritesService
      .criar({
        tmdb_movie_id: filme.tmdb_movie_id,
        titulo: filme.titulo,
        poster_path: this.posterPath(filme),
      })
      .subscribe({
        next: (favorito) => this.favoritos.update((atual) => [favorito, ...atual]),
        error: () => this.carregarFavoritos(),
      });
  }
}
