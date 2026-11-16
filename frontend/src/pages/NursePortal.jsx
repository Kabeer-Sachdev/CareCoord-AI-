import React, { useState, useEffect, useCallback } from 'react';
import { 
  Heart, 
  BedDouble, 
  Siren, 
  ArrowRightLeft, 
  CheckCircle, 
  AlertCircle, 
  RefreshCw,
  Plus,
  Activity,
  Layers
} from 'lucide-react';
import { apiService } from '../services/api';
import { wsClient } from '../services/websocket';

export function NursePortal() {
  const [beds, setBeds] = useState([]);
  const [emergencies, setEmergencies] = useState([]);
  const [loading, setLoading] = useState(true);

  // Transfer Form State
  const [transferForm, setTransferForm] = useState({
    patient_id: '',
    from_bed_id: '',
    to_bed_id: '',
    reason: ''
  });
  const [transferLoading, setTransferLoading] = useState(false);
  const [transferMsg, setTransferMsg] = useState('');

  // Bed Status Action State
  const [selectedBed, setSelectedBed] = useState(null);
  const [assignPatientId, setAssignPatientId] = useState('');

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [allBeds, allEmergencies] = await Promise.all([
        apiService.getBeds().catch(() => []),
        apiService.getEmergencies().catch(() => [])
      ]);
      setBeds(Array.isArray(allBeds) ? allBeds : []);
      setEmergencies(Array.isArray(allEmergencies) ? allEmergencies : []);
    } catch (err) {
      console.error('Failed to load nurse portal data', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();

    const unsubBed = wsClient.on('BED_STATUS_CHANGED', () => loadData());
    const unsubTransferred = wsClient.on('BED_TRANSFERRED', () => loadData());
    const unsubEmergency = wsClient.on('EMERGENCY_CREATED', () => loadData());
    const unsubEmgUpdated = wsClient.on('EMERGENCY_UPDATED', () => loadData());

    return () => {
      unsubBed();
      unsubTransferred();
      unsubEmergency();
      unsubEmgUpdated();
    };
  }, [loadData]);

  const handleUpdateBed = async (bedId, newStatus, patientId = null) => {
    try {
      await apiService.updateBedStatus(bedId, newStatus, patientId, 'Updated from Nurse Station');
      setSelectedBed(null);
      setAssignPatientId('');
      await loadData();
    } catch (err) {
      alert(err.message || 'Bed status update failed');
    }
  };

  const handleTransfer = async (e) => {
    e.preventDefault();
    if (!transferForm.patient_id || !transferForm.from_bed_id || !transferForm.to_bed_id) {
      setTransferMsg('Please fill out all required fields');
      return;
    }
    setTransferLoading(true);
    setTransferMsg('');
    try {
      await apiService.transferPatient(transferForm);
      setTransferMsg('✓ Patient successfully transferred!');
      setTransferForm({ patient_id: '', from_bed_id: '', to_bed_id: '', reason: '' });
      await loadData();
      setTimeout(() => setTransferMsg(''), 4000);
    } catch (err) {
      setTransferMsg(`Transfer failed: ${err.message}`);
    } finally {
      setTransferLoading(false);
    }
  };

  const handleEmergencyAction = async (emergencyId, status) => {
    try {
      await apiService.updateEmergency(emergencyId, { status });
      await loadData();
    } catch (err) {
      alert(err.message || 'Action failed');
    }
  };

  // KPIs
  const totalBeds = beds.length;
  const availableBeds = beds.filter(b => b.status === 'available').length;
  const icuAvailable = beds.filter(b => b.bed_type === 'ICU' && b.status === 'available').length;
  const activeEmergencies = emergencies.filter(e => e.status !== 'completed');

  // Group beds by type
  const bedGroups = ['ICU', 'Emergency', 'General', 'Private'].reduce((acc, type) => {
    acc[type] = beds.filter(b => b.bed_type?.toLowerCase() === type.toLowerCase());
    return acc;
  }, {});

  const statusBadge = {
    available: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    occupied: 'bg-red-500/10 text-red-400 border-red-500/30',
    reserved: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    maintenance: 'bg-gray-500/10 text-gray-400 border-gray-500/30'
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-dark-800 border border-dark-700/80 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-gradient-to-tr from-amber-500 to-orange-600 rounded-xl text-white shadow-lg shadow-amber-500/20">
            <Heart className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-white tracking-tight">Nurse Station & Ward Management</h1>
              <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-amber-500/10 text-amber-400 border border-amber-500/20">
                STATION-NORTH
              </span>
            </div>
            <p className="text-xs text-gray-400 mt-0.5">Bed allocation, patient step-down transfers, and active emergency triage</p>
          </div>
        </div>
        <button
          onClick={loadData}
          className="p-2 bg-dark-700 hover:bg-dark-600 rounded-lg text-gray-300 border border-dark-600 transition-colors self-start md:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-amber-400' : ''}`} />
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-dark-800 border border-dark-700/80 rounded-xl p-4">
          <div className="flex items-center justify-between text-gray-400 text-xs">
            <span>Total Beds</span>
            <BedDouble className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-2">{totalBeds}</div>
          <div className="text-[10px] text-gray-500 mt-1 font-mono">All wards & floors</div>
        </div>

        <div className="bg-dark-800 border border-dark-700/80 rounded-xl p-4">
          <div className="flex items-center justify-between text-gray-400 text-xs">
            <span>Available Beds</span>
            <CheckCircle className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-2">{availableBeds}</div>
          <div className="text-[10px] text-gray-500 mt-1 font-mono">{Math.round((availableBeds / (totalBeds || 1)) * 100)}% vacancy</div>
        </div>

        <div className="bg-dark-800 border border-dark-700/80 rounded-xl p-4">
          <div className="flex items-center justify-between text-gray-400 text-xs">
            <span>ICU Available</span>
            <Activity className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-2">{icuAvailable}</div>
          <div className="text-[10px] text-gray-500 mt-1 font-mono">Critical care units</div>
        </div>

        <div className="bg-dark-800 border border-dark-700/80 rounded-xl p-4">
          <div className="flex items-center justify-between text-gray-400 text-xs">
            <span>Active Emergencies</span>
            <Siren className="w-4 h-4 text-red-400 animate-pulse" />
          </div>
          <div className="text-2xl font-bold text-white mt-2">{activeEmergencies.length}</div>
          <div className="text-[10px] text-gray-500 mt-1 font-mono">In triage or waiting</div>
        </div>
      </div>

      {/* Patient Bed Transfer Tool */}
      <div className="bg-dark-800 border border-dark-700/80 rounded-2xl p-6 shadow-xl">
        <h2 className="text-base font-bold text-white tracking-tight flex items-center gap-2 mb-1">
          <ArrowRightLeft className="w-4 h-4 text-amber-400" />
          <span>Patient Bed Transfer Tool</span>
        </h2>
        <p className="text-xs text-gray-400 mb-4">Transfer an admitted patient between wards or step down from ICU</p>

        {transferMsg && (
          <div className={`p-3 rounded-lg text-xs mb-4 font-mono ${transferMsg.startsWith('✓') ? 'bg-emerald-950/60 text-emerald-300 border border-emerald-800' : 'bg-red-950/60 text-red-300 border border-red-800'}`}>
            {transferMsg}
          </div>
        )}

        <form onSubmit={handleTransfer} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
          <div>
            <label className="block text-gray-300 mb-1 font-medium">Patient ID</label>
            <input
              type="text"
              required
              placeholder="e.g. P001"
              value={transferForm.patient_id}
              onChange={(e) => setTransferForm({ ...transferForm, patient_id: e.target.value })}
              className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-white font-mono"
            />
          </div>

          <div>
            <label className="block text-gray-300 mb-1 font-medium">Current Bed (From)</label>
            <input
              type="text"
              required
              placeholder="e.g. B001"
              value={transferForm.from_bed_id}
              onChange={(e) => setTransferForm({ ...transferForm, from_bed_id: e.target.value })}
              className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-white font-mono"
            />
          </div>

          <div>
            <label className="block text-gray-300 mb-1 font-medium">Destination Bed (To)</label>
            <input
              type="text"
              required
              placeholder="e.g. B010"
              value={transferForm.to_bed_id}
              onChange={(e) => setTransferForm({ ...transferForm, to_bed_id: e.target.value })}
              className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-white font-mono"
            />
          </div>

          <div>
            <label className="block text-gray-300 mb-1 font-medium">Reason / Clinical Note</label>
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="e.g. ICU step-down"
                value={transferForm.reason}
                onChange={(e) => setTransferForm({ ...transferForm, reason: e.target.value })}
                className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-white"
              />
              <button
                type="submit"
                disabled={transferLoading}
                className="px-4 py-2 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white font-semibold rounded-lg shrink-0 transition-all"
              >
                {transferLoading ? '...' : 'Transfer'}
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Bed Allocation Grid */}
      <div className="space-y-4">
        <h2 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
          <Layers className="w-4 h-4 text-cyan-400" />
          <span>Hospital Ward Bed Grid</span>
        </h2>

        {Object.entries(bedGroups).map(([type, typeBeds]) => (
          <div key={type} className="bg-dark-800 border border-dark-700/80 rounded-2xl p-5 shadow-xl">
            <div className="flex items-center justify-between mb-3 border-b border-dark-700 pb-2">
              <h3 className="text-sm font-semibold text-white">{type} Beds ({typeBeds.length})</h3>
              <span className="text-xs text-gray-400 font-mono">
                {typeBeds.filter(b => b.status === 'available').length} Available
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 lg:grid-cols-6 gap-3">
              {typeBeds.map(bed => (
                <div
                  key={bed.bed_id}
                  className="p-3 bg-dark-900 border border-dark-700 rounded-xl flex flex-col justify-between hover:border-dark-600 transition-all text-xs"
                >
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-mono font-bold text-white">{bed.bed_id}</span>
                      <span className="text-[10px] text-gray-500 font-mono">Fl.{bed.floor}</span>
                    </div>
                    <div className="text-[11px] text-gray-400 truncate">{bed.ward}</div>
                    <span className={`inline-block mt-2 px-1.5 py-0.5 rounded text-[10px] font-mono border ${statusBadge[bed.status] || 'bg-gray-800 text-gray-400'}`}>
                      {bed.status}
                    </span>
                    {bed.patient_id && (
                      <div className="mt-1 text-[11px] text-cyan-400 font-mono">
                        👤 {bed.patient_id}
                      </div>
                    )}
                  </div>

                  {/* Bed Action buttons */}
                  <div className="mt-3 pt-2 border-t border-dark-700/50 flex flex-wrap gap-1">
                    {bed.status === 'available' ? (
                      <button
                        onClick={() => setSelectedBed(bed.bed_id)}
                        className="w-full py-1 px-1.5 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded text-[10px] font-medium"
                      >
                        Assign Patient
                      </button>
                    ) : bed.status === 'occupied' ? (
                      <button
                        onClick={() => handleUpdateBed(bed.bed_id, 'available')}
                        className="w-full py-1 px-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 rounded text-[10px] font-medium"
                      >
                        Discharge / Free
                      </button>
                    ) : (
                      <button
                        onClick={() => handleUpdateBed(bed.bed_id, 'available')}
                        className="w-full py-1 px-1.5 bg-gray-700 hover:bg-gray-600 text-gray-200 rounded text-[10px]"
                      >
                        Set Ready
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Assign Patient Modal */}
      {selectedBed && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-dark-800 border border-dark-700 rounded-2xl p-5 max-w-sm w-full shadow-2xl">
            <h3 className="text-sm font-bold text-white mb-2">Assign Patient to Bed {selectedBed}</h3>
            <p className="text-xs text-gray-400 mb-4">Enter patient identifier to occupy this bed.</p>

            <input
              type="text"
              placeholder="e.g. P001"
              value={assignPatientId}
              onChange={(e) => setAssignPatientId(e.target.value)}
              className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-xs text-white font-mono mb-4"
            />

            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setSelectedBed(null)}
                className="px-3 py-1.5 bg-dark-700 hover:bg-dark-600 text-gray-300 rounded-lg text-xs"
              >
                Cancel
              </button>
              <button
                onClick={() => handleUpdateBed(selectedBed, 'occupied', assignPatientId)}
                disabled={!assignPatientId.trim()}
                className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-semibold rounded-lg text-xs"
              >
                Confirm Allocation
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}