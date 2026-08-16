import { CommonModule } from '@angular/common';
import { Component, OnInit, signal } from '@angular/core';

import { FavoritesService } from '../../core/services/favorites.service';
import { MoviesService } from '../../core/services/movies.service';
import { Favorite } from '../../models/favorite.model';
import { Movie } from '../../models/movie.model';
import { MovieCard } from '../../shared/movie-card/movie-card';

@Component({
  selector: 'app-catalog',
  standalone: true,
  imports: [CommonModule, MovieCard],
  templateUrl: './catalog.html',
  styleUrl: './catalog.css',
})
export class Catalog implements OnInit {
  filmes = signal<Movie[]>([]);
  favoritos = signal<Favorite[]>([]);
  carregando = signal(true);
  erro = signal('');

  constructor(
    private readonly moviesService: MoviesService,
    private readonly favoritesService: FavoritesService,
  ) {}

  ngOnInit(): void {
    this.carregarFavoritos();
    this.carregarFilmes();
  }

  private carregarFilmes(): void {
    this.carregando.set(true);
    this.moviesService.listar().subscribe({
      next: (filmes) => {
        this.filmes.set(filmes);
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
