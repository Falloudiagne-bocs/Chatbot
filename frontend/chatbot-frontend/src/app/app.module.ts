import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';

// Importation des composants standalone
import { AppComponent } from './app.component';
import { ChatComponent } from './chat/chat.component';

@NgModule({
  imports: [
    BrowserModule,
    FormsModule,
    HttpClientModule,
    AppComponent,      // 👈 import standalone component
    ChatComponent      // 👈 import standalone component
  ],
  bootstrap: [AppComponent],
})
export class AppModule {}
