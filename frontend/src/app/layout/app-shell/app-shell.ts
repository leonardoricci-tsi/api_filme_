import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { Header } from '../header/header';

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [RouterOutlet, Header],
  templateUrl: './app-shell.html',
  styleUrl: './app-shell.css',
})
export class AppShell {}
