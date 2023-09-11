import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class LanguageService {
  private languageKey = 'language';

  getLanguage(): string | null {
    return localStorage.getItem(this.languageKey);
  }

  setLanguage(language: string): void {
    localStorage.setItem(this.languageKey, language);
  }

  // Add other language-related methods here
}
