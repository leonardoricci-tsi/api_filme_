import { CommonModule } from '@angular/common';
import { Component, signal } from '@angular/core';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';

import { AuthService } from '../../core/services/auth.service';

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
export class Header {
  readonly menuAberto = signal(false);

  constructor(
    readonly authService: AuthService,
    private readonly router: Router,
  ) {}

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
    this.menuAberto.set(false);
    this.router.navigate(['/']);
  }
}
