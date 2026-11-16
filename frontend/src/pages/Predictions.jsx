import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  Activity,
  BedDouble,
  Calendar,
  Siren,
  ShieldAlert,
  Sparkles,
  RefreshCw,
  Layers,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  BarChart3,
  ArrowRight,
  Clock,
  Filter
} from 'lucide-react';
import { apiService } from '../services/api';

export function PredictionsPage() {
  const [forecastDate, setForecastDate] = useState(() => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toISOString().split('T')[0];
  });
  const [selectedDept, setSelectedDept] = useState('All');
  const [overview, setOverview] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRetraining, setIsRetraining] = useState(false);
  const [error, setError] = useState(null);
  const [retrainSuccess, setRetrainSuccess] = useState(null);

  const userRole = localStorage.getItem('cc_role') || 'ADMIN';

  const fetchData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [overviewData, metricsData] = await Promise.all([
        apiService.getMlOverview(forecastDate),
        apiService.getMlMetrics()
      ]);
      setOverview(overviewData);
      setMetrics(metricsData);
    } catch (err) {
      setError(err.message || 'Failed to load predictive analytics data.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [forecastDate]);

  const handleRetrain = async () => {
    if (!window.confirm('Initiate chronological retraining of all 4 hospital resource forecasting models?')) return;
    setIsRetraining(true);
    setRetrainSuccess(null);
    setError(null);
    try {
      const res = await apiService.trainMlModels();
      setRetrainSuccess(`Models successfully retrained! Trained on ${res.metrics.train_records} records.`);
      await fetchData();
    } catch (err) {
      setError(err.message || 'Model retraining failed.');
    } finally {
      setIsRetraining(false);
    }
  };

  const handleQuickDate = (daysFromNow) => {
    const d = new Date();
    d.setDate(d.getDate() + daysFromNow);
    setForecastDate(d.toISOString().split('T')[0]);
  };

  const filteredBreakdown = overview?.department_breakdown?.filter((dept) => {
    if (selectedDept === 'All') return true;
    return dept.department.toLowerCase() === selectedDept.toLowerCase();
  }) || [];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gray-900 border border-gray-800 p-6 rounded-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl -z-10"></div>
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 flex items-center gap-1.5">
              <Sparkles className="w-3 h-3 text-cyan-400" /> Phase 6 Machine Learning
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5">
              <Cpu className="w-3 h-3 text-emerald-400" /> Scikit-Learn Regression Pipeline
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <TrendingUp className="w-7 h-7 text-cyan-400" /> Predictive Resource Demand Command Center
          </h1>
          <p className="text-sm text-gray-400 mt-1 max-w-2xl">
            Anticipate hospital operational workload 24–72 hours in advance using gradient boosting and random forest time-series models trained on chronological hospital records.
          </p>
        </div>

        {/* Date and Retrain Controls */}
        <div className="flex flex-wrap items-center gap-2.5 self-start md:self-auto">
          <div className="flex items-center bg-gray-950 border border-gray-800 rounded-xl p-1 text-xs">
            <button
              onClick={() => handleQuickDate(1)}
              className="px-2.5 py-1.5 rounded-lg text-gray-300 hover:text-white hover:bg-gray-800 font-medium transition-colors"
            >
              Tomorrow
            </button>
            <button
              onClick={() => handleQuickDate(3)}
              className="px-2.5 py-1.5 rounded-lg text-gray-300 hover:text-white hover:bg-gray-800 font-medium transition-colors"
            >
              +3 Days
            </button>
            <button
              onClick={() => handleQuickDate(7)}
              className="px-2.5 py-1.5 rounded-lg text-gray-300 hover:text-white hover:bg-gray-800 font-medium transition-colors"
            >
              +7 Days
            </button>
          </div>

          <input
            type="date"
            value={forecastDate}
            onChange={(e) => setForecastDate(e.target.value)}
            className="bg-gray-950 border border-gray-800 text-white rounded-xl px-3 py-2 text-xs focus:outline-none focus:border-cyan-500 font-mono"
          />

          {userRole === 'ADMIN' && (
            <button
              onClick={handleRetrain}
              disabled={isRetraining}
              className="px-3.5 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-black font-semibold text-xs rounded-xl shadow-lg shadow-cyan-500/20 hover:opacity-95 transition-all flex items-center gap-1.5 disabled:opacity-50"
            >
              {isRetraining ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Retraining...
                </>
              ) : (
                <>
                  <RefreshCw className="w-3.5 h-3.5" /> Retrain ML
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Retrain Success Notification */}
      {retrainSuccess && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-xs text-emerald-400 flex items-center gap-2.5">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>{retrainSuccess}</span>
        </div>
      )}

      {/* Global Error Banner */}
      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-xs text-rose-400 flex items-center gap-2.5">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Section A: Executive KPI Forecast Overview */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-28 bg-gray-900 border border-gray-800 rounded-2xl animate-pulse"></div>
          ))}
        </div>
      ) : overview && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Predicted Arrivals */}
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-2 relative overflow-hidden">
            <div className="flex items-center justify-between text-xs text-gray-400">
              <span className="font-semibold uppercase tracking-wider">Patient Arrivals</span>
              <Activity className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="text-3xl font-bold text-white font-mono">
              {overview.total_predicted_arrivals}
            </div>
            <div className="text-[11px] text-gray-400 flex items-center gap-1">
              <span>Expected on <strong className="text-gray-300">{overview.forecast_date}</strong></span>
            </div>
          </div>

          {/* Predicted Emergencies */}
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-2 relative overflow-hidden">
            <div className="flex items-center justify-between text-xs text-gray-400">
              <span className="font-semibold uppercase tracking-wider">Emergency Workload</span>
              <Siren className="w-4 h-4 text-rose-400" />
            </div>
            <div className="text-3xl font-bold text-rose-400 font-mono">
              {overview.total_predicted_emergencies}
            </div>
            <div className="text-[11px] text-gray-400">
              <span>Estimated ER / Trauma cases</span>
            </div>
          </div>

          {/* Hospital Bed Occupancy */}
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-2 relative overflow-hidden">
            <div className="flex items-center justify-between text-xs text-gray-400">
              <span className="font-semibold uppercase tracking-wider">Bed Occupancy</span>
              <BedDouble className="w-4 h-4 text-amber-400" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-white font-mono">
                {Math.round(overview.hospital_occupancy_rate * 100)}%
              </span>
              <span className="text-xs text-gray-400 font-mono">
                ({overview.total_occupied_beds}/{overview.total_beds} beds)
              </span>
            </div>
            <div className="w-full bg-gray-800 h-1.5 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${
                  overview.hospital_occupancy_rate >= 0.85
                    ? 'bg-rose-500'
                    : overview.hospital_occupancy_rate >= 0.70
                    ? 'bg-amber-500'
                    : 'bg-emerald-500'
                }`}
                style={{ width: `${Math.min(100, overview.hospital_occupancy_rate * 100)}%` }}
              ></div>
            </div>
          </div>

          {/* Appointment Demand */}
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-2 relative overflow-hidden">
            <div className="flex items-center justify-between text-xs text-gray-400">
              <span className="font-semibold uppercase tracking-wider">Appointments</span>
              <Calendar className="w-4 h-4 text-blue-400" />
            </div>
            <div className="text-3xl font-bold text-white font-mono">
              {overview.total_predicted_appointments}
            </div>
            <div className="text-[11px] text-gray-400">
              <span>Forecasted consultations</span>
            </div>
          </div>
        </div>
      )}

      {/* Section B: Operational Alerts & Early Warnings */}
      {overview?.operational_alerts && overview.operational_alerts.length > 0 && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-2xl p-4 space-y-2">
          <div className="flex items-center gap-2 text-xs font-semibold text-amber-400 uppercase tracking-wider">
            <ShieldAlert className="w-4 h-4" /> Operational Early Warning Alerts ({overview.operational_alerts.length})
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {overview.operational_alerts.map((alert, idx) => (
              <div
                key={idx}
                className="p-2.5 bg-gray-950/60 border border-amber-500/20 rounded-xl text-xs text-amber-200 flex items-center gap-2"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 flex-shrink-0"></span>
                <span>{alert}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Section C: Department-wise Predictive Breakdown */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-cyan-400" /> Department-Wise Operational Forecast
            </h2>
            <p className="text-xs text-gray-400 mt-0.5">
              Specific resource demands per clinical department for {forecastDate}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-gray-400" />
            <select
              value={selectedDept}
              onChange={(e) => setSelectedDept(e.target.value)}
              className="bg-gray-950 border border-gray-800 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500"
            >
              <option value="All">All Departments</option>
              <option value="Cardiology">Cardiology</option>
              <option value="Neurology">Neurology</option>
              <option value="Orthopedics">Orthopedics</option>
              <option value="General Medicine">General Medicine</option>
              <option value="Emergency Medicine">Emergency Medicine</option>
              <option value="Pediatrics">Pediatrics</option>
              <option value="Dermatology">Dermatology</option>
            </select>
          </div>
        </div>

        {/* Department Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredBreakdown.map((dept, idx) => (
            <div
              key={idx}
              className="bg-gray-950 border border-gray-800/80 rounded-xl p-4 space-y-3 hover:border-gray-700 transition-colors"
            >
              <div className="flex items-center justify-between pb-2 border-b border-gray-800">
                <span className="text-sm font-semibold text-white">{dept.department}</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold ${
                  dept.occupancy_rate >= 0.85
                    ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                    : dept.occupancy_rate >= 0.70
                    ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                    : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                }`}>
                  {Math.round(dept.occupancy_rate * 100)}% Bed Occupancy
                </span>
              </div>

              {/* Department Metrics */}
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="p-2 bg-gray-900 rounded-lg">
                  <span className="text-[10px] text-gray-400 block uppercase">Arrivals</span>
                  <span className="text-base font-bold text-white font-mono">{dept.predicted_arrivals}</span>
                </div>
                <div className="p-2 bg-gray-900 rounded-lg">
                  <span className="text-[10px] text-gray-400 block uppercase">ER Cases</span>
                  <span className="text-base font-bold text-rose-400 font-mono">{dept.predicted_emergencies}</span>
                </div>
                <div className="p-2 bg-gray-900 rounded-lg">
                  <span className="text-[10px] text-gray-400 block uppercase">Appts</span>
                  <span className="text-base font-bold text-cyan-400 font-mono">{dept.predicted_appointments}</span>
                </div>
              </div>

              {/* Bed Utilization Bar */}
              <div className="space-y-1">
                <div className="flex items-center justify-between text-[11px] text-gray-400 font-mono">
                  <span>Occupied Beds: <strong className="text-gray-200">{dept.predicted_occupied_beds}</strong> / {dept.total_beds}</span>
                  <span className="text-emerald-400">{dept.estimated_available_beds} Available</span>
                </div>
                <div className="w-full bg-gray-800 h-1.5 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      dept.occupancy_rate >= 0.85 ? 'bg-rose-500' : dept.occupancy_rate >= 0.70 ? 'bg-amber-500' : 'bg-emerald-500'
                    }`}
                    style={{ width: `${Math.min(100, dept.occupancy_rate * 100)}%` }}
                  ></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Section D: ML Model Comparison & Governance Report */}
      {metrics && metrics.targets && (
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-gray-800">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Cpu className="w-5 h-5 text-cyan-400" /> Machine Learning Model Governance & Benchmark Comparison
              </h2>
              <p className="text-xs text-gray-400 mt-0.5">
                Evaluated on untouched test split (196 observations, chronologically isolated). Zero PII exposure.
              </p>
            </div>
            <span className="text-xs font-mono text-gray-400 flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5" /> Trained: {new Date(metrics.training_timestamp).toLocaleDateString()}
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-gray-800 bg-gray-950/60 text-gray-400 uppercase font-semibold">
                  <th className="py-3 px-4">Prediction Task</th>
                  <th className="py-3 px-4">Selected Winning Model</th>
                  <th className="py-3 px-4 text-center">Baseline Test MAE</th>
                  <th className="py-3 px-4 text-center">Winning Test MAE</th>
                  <th className="py-3 px-4 text-center">Test RMSE</th>
                  <th className="py-3 px-4 text-center">Test R²</th>
                  <th className="py-3 px-4 text-right">Performance Gain</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800 text-gray-300">
                {Object.entries(metrics.targets).map(([key, item]) => {
                  const baseMae = item.models_comparison?.BaselineMovingAverage?.test?.mae || 0;
                  const winMae = item.selected_metrics?.test?.mae || 0;
                  const winRmse = item.selected_metrics?.test?.rmse || 0;
                  const winR2 = item.selected_metrics?.test?.r2 || 0;
                  const pctImprovement = baseMae > 0 ? Math.round(((baseMae - winMae) / baseMae) * 100) : 0;

                  return (
                    <tr key={key} className="hover:bg-gray-800/40 transition-colors">
                      <td className="py-3 px-4 font-semibold text-white">{item.target_name}</td>
                      <td className="py-3 px-4 font-mono text-cyan-400">
                        {item.selected_model} <span className="text-[10px] text-gray-400 font-sans">(v1.0)</span>
                      </td>
                      <td className="py-3 px-4 text-center font-mono text-gray-400">{baseMae}</td>
                      <td className="py-3 px-4 text-center font-mono text-emerald-400 font-semibold">{winMae}</td>
                      <td className="py-3 px-4 text-center font-mono text-gray-300">{winRmse}</td>
                      <td className="py-3 px-4 text-center font-mono text-gray-300">{winR2}</td>
                      <td className="py-3 px-4 text-right">
                        <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-mono font-semibold text-[11px]">
                          +{pctImprovement}% vs Baseline
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="p-3 bg-blue-500/5 border border-blue-500/20 rounded-xl flex items-start gap-2.5">
            <ShieldAlert className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
            <span className="text-[11px] text-blue-300/80 leading-normal">
              <strong>Clinical & Operational Safety Notice:</strong> Forecast outputs represent statistical estimates designed strictly for hospital logistics, staff scheduling, and bed preparation. They do not dictate medical treatments, patient admission refusals, or automated bed reallocations.
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
