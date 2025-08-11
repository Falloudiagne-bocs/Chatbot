import 'zone.js';
import { bootstrapApplication } from '@angular/platform-browser';
import { AppComponent } from './app/app.component';
import { provideHttpClient } from '@angular/common/http';
import { provideMarkdown } from 'ngx-markdown';  

bootstrapApplication(AppComponent, {
  providers: [
    provideHttpClient(),       
    provideMarkdown()         
  ]
});
