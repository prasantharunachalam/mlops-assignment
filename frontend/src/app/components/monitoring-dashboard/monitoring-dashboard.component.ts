import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTableModule } from '@angular/material/table';
import { MonitoringService, ModelService } from '../../services';
import { MetricSnapshot } from '../../models';

@Component({
  selector: 'app-monitoring-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatCardModule,
    MatFormFieldModule,
    MatSelectModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatInputModule,
    MatButtonModule,
    MatProgressSpinnerModule,
    MatTableModule
  ],
  templateUrl: './monitoring-dashboard.component.html',
  styleUrl: './monitoring-dashboard.component.scss'
})
export class MonitoringDashboardComponent implements OnInit {
  filterForm: FormGroup;
  loading = false;
  metricsLoaded = false;
  metrics: MetricSnapshot[] = [];
  modelVersions: Array<{ model_id: string; version_id: string; model_name: string; version_number: string }> = [];

  displayedColumns: string[] = ['captured_at', 'latency_ms', 'throughput_rps', 'error_rate', 'quality_score', 'drift_score', 'availability'];

  // Summary statistics
  avgLatency: number | null = null;
  avgThroughput: number | null = null;
  avgErrorRate: number | null = null;
  avgQuality: number | null = null;
  avgDrift: number | null = null;
  avgAvailability: number | null = null;

  constructor(
    private fb: FormBuilder,
    private monitoringService: MonitoringService,
    private modelService: ModelService
  ) {
    const now = new Date();
    const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);

    this.filterForm = this.fb.group({
      modelVersion: ['', Validators.required],
      startTime: [oneHourAgo, Validators.required],
      endTime: [now, Validators.required]
    });
  }

  ngOnInit() {
    this.loadModelVersions();
  }

  loadModelVersions() {
    this.modelService.listModels().subscribe({
      next: (response) => {
        const versionPromises = response.items.map(model =>
          new Promise((resolve) => {
            this.modelService.listVersions(model.id).subscribe({
              next: (versionResponse) => {
                const versions = versionResponse.items.map(v => ({
                  model_id: model.id,
                  version_id: v.id,
                  model_name: model.name,
                  version_number: v.version_number
                }));
                resolve(versions);
              },
              error: () => resolve([])
            });
          })
        );

        Promise.all(versionPromises).then((allVersions: any) => {
          this.modelVersions = allVersions.flat();
        });
      }
    });
  }

  loadMetrics() {
    if (this.filterForm.valid) {
      this.loading = true;
      const { modelVersion, startTime, endTime } = this.filterForm.value;
      const [model_id, version_id] = modelVersion.split('|');

      this.monitoringService.getMetrics(
        model_id,
        version_id,
        startTime.toISOString(),
        endTime.toISOString()
      ).subscribe({
        next: (response) => {
          this.metrics = response.items;
          this.metricsLoaded = true;
          this.calculateSummaryStats();
          this.loading = false;
        },
        error: (error) => {
          console.error('Error loading metrics:', error);
          this.metricsLoaded = true;
          this.loading = false;
        }
      });
    }
  }

  calculateSummaryStats() {
    if (this.metrics.length === 0) {
      this.resetStats();
      return;
    }

    const sum = (arr: (number | undefined)[]) =>
      arr.filter(v => v !== undefined && v !== null).reduce((a, b) => a! + b!, 0);
    const avg = (arr: (number | undefined)[]) => {
      const filtered = arr.filter(v => v !== undefined && v !== null);
      return filtered.length > 0 ? sum(filtered)! / filtered.length : null;
    };

    this.avgLatency = avg(this.metrics.map(m => m.latency_ms));
    this.avgThroughput = avg(this.metrics.map(m => m.throughput_rps));
    this.avgErrorRate = avg(this.metrics.map(m => m.error_rate));
    this.avgQuality = avg(this.metrics.map(m => m.quality_score));
    this.avgDrift = avg(this.metrics.map(m => m.drift_score));
    this.avgAvailability = avg(this.metrics.map(m => m.availability));
  }

  resetStats() {
    this.avgLatency = null;
    this.avgThroughput = null;
    this.avgErrorRate = null;
    this.avgQuality = null;
    this.avgDrift = null;
    this.avgAvailability = null;
  }

  getVersionDisplay(version: any): string {
    return `${version.model_name} v${version.version_number}`;
  }
}
