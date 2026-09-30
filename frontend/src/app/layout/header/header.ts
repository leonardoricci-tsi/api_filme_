import { CommonModule } from '@angular/common';
import { Component, OnInit, signal } from '@angular/core';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';

import { AuthService } from '../../core/services/auth.service';
import { ProfileService } from '../../core/services/profile.service';

const NOME_PAPEL: Record<string, string> = {
  cinefilo: 'Cinéfilo',
  nerd: 'Nerd',
  stalker_do_tomhanks: 'Stalker do Tom Hanks',
  admin: 'Admin',
};

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive],
  templateUrl: './header.html',
  styleUrl: './header.css',
})
export class Header implements OnInit {
  readonly menuAberto = signal(false);

  constructor(
    readonly authService: AuthService,
    readonly profileService: ProfileService,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    // O header só existe dentro da área logada (AppShell), então aqui
    // sempre há um usuário — busca a foto dele uma vez, pro avatar.
    const id = this.authService.usuarioId();
    if (id !== null) {
      this.profileService.carregarMinhaFoto(id);
    }
  }

  get iniciais(): string {
    const nome = this.authService.usuario()?.nome ?? '?';
    return nome.trim().charAt(0).toUpperCase();
  }

  get nomePapel(): string {
    const papel = this.authService.usuario()?.role ?? '';
    return NOME_PAPEL[papel] ?? papel;
  }

  toggleMenu(): void {
    this.menuAberto.update((aberto) => !aberto);
  }

  sair(): void {
    this.authService.logout();
    this.profileService.limparMinhaFoto();
    this.menuAberto.set(false);
    this.router.navigate(['/']);
  }
}
