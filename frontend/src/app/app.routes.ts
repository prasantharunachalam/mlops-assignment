import { Routes } from '@angular/router';
import { ModelsListComponent } from './components/models-list/models-list.component';
import { ModelDetailComponent } from './components/model-detail/model-detail.component';
import { DeploymentsListComponent } from './components/deployments-list/deployments-list.component';
import { MonitoringDashboardComponent } from './components/monitoring-dashboard/monitoring-dashboard.component';

export const routes: Routes = [
  { path: '', redirectTo: '/models', pathMatch: 'full' },
  { path: 'models', component: ModelsListComponent },
  { path: 'models/:id', component: ModelDetailComponent },
  { path: 'deployments', component: DeploymentsListComponent },
  { path: 'monitoring', component: MonitoringDashboardComponent }
];
