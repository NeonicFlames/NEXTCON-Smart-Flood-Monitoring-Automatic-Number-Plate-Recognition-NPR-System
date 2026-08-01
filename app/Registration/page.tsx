"use client";

import { useEffect, useState } from "react";
import AdminGuard from "@/components/AdminGuard";
import {
  getRegisteredVehicles,
  addRegisteredVehicle,
  deleteRegisteredVehicle,
  toggleRegisteredVehicleStatus,
  NewVehicleInput,
} from "@/lib/queries/vehicles";
import {
  Car,
  Plus,
  Search,
  Trash2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  UserCheck,
  ShieldCheck,
  Building2,
  RefreshCw,
  Phone,
  Mail
} from "lucide-react";

interface RegisteredVehicle {
  id: string;
  plate_number: string;
  owner_name: string;
  phone?: string;
  email?: string;
  vehicle_type?: string;
  zone?: string;
  is_active: boolean;
  created_at: string;
}

export default function RegistrationPage() {
  const [vehicles, setVehicles] = useState<RegisteredVehicle[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedStatus, setSelectedStatus] = useState("ALL");

  // Modal states
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Form input state
  const [formData, setFormData] = useState<NewVehicleInput>({
    plate_number: "",
    owner_name: "",
    phone: "",
    email: "",
    vehicle_type: "Car",
    is_active: true,
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await getRegisteredVehicles();
      setVehicles((data as RegisteredVehicle[]) || []);
    } catch (err) {
      console.error("Failed to fetch registered vehicles:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.plate_number.trim() || !formData.owner_name.trim()) return;

    setSubmitting(true);
    try {
      const created = await addRegisteredVehicle(formData);
      setVehicles((prev) => [created as RegisteredVehicle, ...prev]);
      setIsAddModalOpen(false);
      setFormData({
        plate_number: "",
        owner_name: "",
        phone: "",
        email: "",
        vehicle_type: "Car",
        is_active: true,
      });
    } catch (err) {
      console.error("Failed to add vehicle:", err);
      alert("Error adding vehicle. Make sure plate number is valid.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteRegisteredVehicle(id);
      setVehicles((prev) => prev.filter((v) => v.id !== id));
      setDeleteConfirmId(null);
    } catch (err) {
      console.error("Failed to delete vehicle:", err);
      alert("Failed to delete vehicle permit.");
    }
  };

  const handleToggleStatus = async (vehicle: RegisteredVehicle) => {
    const newStatus = !vehicle.is_active;
    try {
      await toggleRegisteredVehicleStatus(vehicle.id, newStatus);
      setVehicles((prev) =>
        prev.map((v) => (v.id === vehicle.id ? { ...v, is_active: newStatus } : v))
      );
    } catch (err) {
      console.error("Failed to toggle vehicle status:", err);
    }
  };

  // Filtered vehicles
  const filteredVehicles = vehicles.filter((v) => {
    const matchesSearch =
      v.plate_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.owner_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (v.phone && v.phone.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesStatus =
      selectedStatus === "ALL" ||
      (selectedStatus === "ACTIVE" && v.is_active) ||
      (selectedStatus === "INACTIVE" && !v.is_active);

    return matchesSearch && matchesStatus;
  });


  const activeCount = vehicles.filter((v) => v.is_active).length;

  return (
    <AdminGuard>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div
              className="p-2.5 rounded-lg shrink-0"
              style={{
                background: "var(--color-paper-2)",
                color: "var(--color-accent)",
                border: "1px solid var(--color-rule)",
              }}
            >
              <Car size={22} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1
                  className="text-xl font-semibold tracking-tight"
                  style={{
                    color: "var(--color-ink)",
                    fontFamily: "var(--font-display)",
                    letterSpacing: "-0.02em",
                  }}
                >
                  Vehicle Permit Registry
                </h1>
                <span
                  className="text-[10px] font-bold px-2 py-0.5 rounded-md uppercase"
                  style={{
                    background: "var(--color-accent-subtle)",
                    color: "var(--color-accent)",
                    border: "1px solid var(--color-rule)",
                  }}
                >
                  Admin Control
                </span>
              </div>
              <p className="mt-0.5 text-sm" style={{ color: "var(--color-neutral)" }}>
                Add, authorize, inspect, and remove registered vehicle permits
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-auto">
            <button
              onClick={loadData}
              className="p-2 rounded-md border text-xs font-medium flex items-center gap-1.5 transition"
              style={{
                background: "var(--color-paper-2)",
                color: "var(--color-neutral)",
                borderColor: "var(--color-rule)",
              }}
              title="Refresh Registry"
            >
              <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            </button>

            <button
              onClick={() => setIsAddModalOpen(true)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-md text-xs font-semibold shadow-sm transition"
              style={{
                background: "var(--color-accent)",
                color: "#ffffff",
              }}
            >
              <Plus size={16} />
              <span>Register New Vehicle</span>
            </button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="card">
            <div className="flex items-center justify-between">
              <p className="text-xs font-medium" style={{ color: "var(--color-neutral)" }}>
                Total Registered Vehicles
              </p>
              <UserCheck size={18} style={{ color: "var(--color-accent)" }} />
            </div>
            <p
              className="text-2xl font-bold mt-2"
              style={{
                color: "var(--color-ink)",
                fontFamily: "var(--font-outlier)",
              }}
            >
              {vehicles.length}
            </p>
          </div>

          <div className="card">
            <div className="flex items-center justify-between">
              <p className="text-xs font-medium" style={{ color: "var(--color-neutral)" }}>
                Active Authorized Permits
              </p>
              <ShieldCheck size={18} style={{ color: "var(--color-safe)" }} />
            </div>
            <p
              className="text-2xl font-bold mt-2"
              style={{
                color: "var(--color-safe)",
                fontFamily: "var(--font-outlier)",
              }}
            >
              {activeCount}
            </p>
          </div>
        </div>

        {/* Search & Filter Toolbar */}
        <div
          className="p-4 rounded-xl border flex flex-col md:flex-row items-center justify-between gap-4"
          style={{
            background: "var(--color-paper-2)",
            borderColor: "var(--color-rule)",
          }}
        >
          {/* Search Input */}
          <div className="relative w-full md:w-80">
            <Search
              size={16}
              className="absolute left-3 top-1/2 -translate-y-1/2"
              style={{ color: "var(--color-muted)" }}
            />
            <input
              type="text"
              placeholder="Search plate number or owner..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-md text-sm border focus:outline-none"
              style={{
                background: "var(--color-paper-3)",
                color: "var(--color-ink)",
                borderColor: "var(--color-rule)",
                fontFamily: "var(--font-outlier)",
              }}
            />
          </div>

          {/* Filters */}
          <div className="flex items-center gap-3 w-full md:w-auto">
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="px-3 py-2 rounded-md text-xs font-medium border focus:outline-none"
              style={{
                background: "var(--color-paper-3)",
                color: "var(--color-ink)",
                borderColor: "var(--color-rule)",
              }}
            >
              <option value="ALL">All Statuses</option>
              <option value="ACTIVE">Active Permits</option>
              <option value="INACTIVE">Suspended / Inactive</option>
            </select>
          </div>
        </div>


        {/* Vehicles Registry Table */}
        <section className="card-flush">
          <div className="px-5 pt-5 pb-3 flex items-center justify-between">
            <h2
              className="text-sm font-semibold"
              style={{ color: "var(--color-ink)" }}
            >
              Registered Vehicles List
            </h2>
            <span
              className="text-xs"
              style={{
                color: "var(--color-muted)",
                fontFamily: "var(--font-outlier)",
              }}
            >
              Showing {filteredVehicles.length} of {vehicles.length} records
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: "1px solid var(--color-rule)" }}>
                  <th className="text-left px-5 py-3 text-xs font-medium text-neutral">
                    Plate Number
                  </th>
                  <th className="text-left px-5 py-3 text-xs font-medium text-neutral">
                    Owner Name
                  </th>
                  <th className="text-left px-5 py-3 text-xs font-medium text-neutral">
                    Contact Details
                  </th>
                  <th className="text-left px-5 py-3 text-xs font-medium text-neutral">
                    Vehicle Type
                  </th>
                  <th className="text-left px-5 py-3 text-xs font-medium text-neutral">
                    Status
                  </th>
                  <th className="text-right px-5 py-3 text-xs font-medium text-neutral">
                    Admin Actions
                  </th>
                </tr>
              </thead>

              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={6} className="px-5 py-8 text-center text-sm text-neutral">
                      Loading vehicle registry data...
                    </td>
                  </tr>
                ) : filteredVehicles.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-5 py-8 text-center text-sm text-neutral">
                      No registered vehicles match your filter criteria.
                    </td>
                  </tr>
                ) : (
                  filteredVehicles.map((vehicle, i) => (
                    <tr
                      key={vehicle.id}
                      style={{
                        borderBottom:
                          i < filteredVehicles.length - 1
                            ? "1px solid var(--color-rule)"
                            : "none",
                      }}
                    >
                      {/* Plate Number */}
                      <td
                        className="px-5 py-3.5 font-bold tracking-wider"
                        style={{
                          color: "var(--color-accent)",
                          fontFamily: "var(--font-outlier)",
                        }}
                      >
                        {vehicle.plate_number}
                      </td>

                      {/* Owner */}
                      <td className="px-5 py-3.5 font-medium" style={{ color: "var(--color-ink)" }}>
                        {vehicle.owner_name}
                      </td>

                      {/* Contact */}
                      <td className="px-5 py-3.5 text-xs text-neutral">
                        <div className="space-y-0.5">
                          {vehicle.phone && (
                            <div className="flex items-center gap-1.5">
                              <Phone size={12} style={{ color: "var(--color-muted)" }} />
                              <span>{vehicle.phone}</span>
                            </div>
                          )}
                          {vehicle.email && (
                            <div className="flex items-center gap-1.5">
                              <Mail size={12} style={{ color: "var(--color-muted)" }} />
                              <span>{vehicle.email}</span>
                            </div>
                          )}
                          {!vehicle.phone && !vehicle.email && <span>—</span>}
                        </div>
                      </td>

                      {/* Type & Zone */}
                      <td className="px-5 py-3.5 text-xs">
                        <div className="font-medium" style={{ color: "var(--color-ink-2)" }}>
                          {vehicle.vehicle_type || "Car"}
                        </div>
                        <div className="text-[11px]" style={{ color: "var(--color-muted)" }}>
                          {vehicle.zone || "Zone A"}
                        </div>
                      </td>

                      {/* Status */}
                      <td className="px-5 py-3.5">
                        <button
                          onClick={() => handleToggleStatus(vehicle)}
                          title="Click to toggle status"
                          className="inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-0.5 rounded-full cursor-pointer hover:opacity-80 transition"
                          style={{
                            background: vehicle.is_active
                              ? "var(--color-safe-subtle)"
                              : "var(--color-warn-subtle)",
                            color: vehicle.is_active
                              ? "var(--color-safe)"
                              : "var(--color-warn)",
                            border: `1px solid ${
                              vehicle.is_active
                                ? "oklch(70% 0.18 145 / 0.2)"
                                : "oklch(78% 0.18 85 / 0.2)"
                            }`,
                          }}
                        >
                          <span
                            className="w-1.5 h-1.5 rounded-full"
                            style={{
                              background: vehicle.is_active
                                ? "var(--color-safe)"
                                : "var(--color-warn)",
                            }}
                          />
                          {vehicle.is_active ? "Active" : "Suspended"}
                        </button>
                      </td>

                      {/* Actions */}
                      <td className="px-5 py-3.5 text-right">
                        <div className="flex items-center justify-end gap-2">
                          {!vehicle.is_active && (
                            <button
                              onClick={() => handleToggleStatus(vehicle)}
                              className="px-2.5 py-1 text-xs font-semibold rounded-md bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm transition flex items-center gap-1"
                              title="Approve and activate this permit"
                            >
                              <CheckCircle2 size={13} />
                              <span>Approve</span>
                            </button>
                          )}
                          <button
                            onClick={() => setDeleteConfirmId(vehicle.id)}
                            className="p-1.5 rounded-md hover:bg-rose-500/10 text-rose-600 transition"
                            title="Remove vehicle permit"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>

                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>

        {/* Modal: Add Vehicle */}
        {isAddModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-150">
            <div
              className="w-full max-w-lg p-6 rounded-xl border shadow-2xl space-y-5"
              style={{
                background: "var(--color-paper-2)",
                borderColor: "var(--color-rule)",
              }}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div
                    className="p-2 rounded-md"
                    style={{
                      background: "var(--color-accent-subtle)",
                      color: "var(--color-accent)",
                    }}
                  >
                    <Car size={20} />
                  </div>
                  <h3
                    className="text-lg font-bold"
                    style={{ color: "var(--color-ink)", fontFamily: "var(--font-display)" }}
                  >
                    Register New Vehicle
                  </h3>
                </div>
                <button
                  onClick={() => setIsAddModalOpen(false)}
                  className="p-1.5 rounded-md text-neutral hover:bg-black/5 dark:hover:bg-white/5"
                >
                  <XCircle size={18} />
                </button>
              </div>

              <form onSubmit={handleAddSubmit} className="space-y-4 text-xs">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block font-medium mb-1" style={{ color: "var(--color-neutral)" }}>
                      Plate Number *
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. WYY 8888"
                      value={formData.plate_number}
                      onChange={(e) =>
                        setFormData({ ...formData, plate_number: e.target.value.toUpperCase() })
                      }
                      className="w-full px-3 py-2 rounded-md border focus:outline-none uppercase font-bold tracking-wider"
                      style={{
                        background: "var(--color-paper-3)",
                        color: "var(--color-accent)",
                        borderColor: "var(--color-rule)",
                        fontFamily: "var(--font-outlier)",
                      }}
                    />
                  </div>

                  <div>
                    <label className="block font-medium mb-1" style={{ color: "var(--color-neutral)" }}>
                      Owner Name *
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="Full owner name"
                      value={formData.owner_name}
                      onChange={(e) => setFormData({ ...formData, owner_name: e.target.value })}
                      className="w-full px-3 py-2 rounded-md border focus:outline-none text-sm"
                      style={{
                        background: "var(--color-paper-3)",
                        color: "var(--color-ink)",
                        borderColor: "var(--color-rule)",
                      }}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block font-medium mb-1" style={{ color: "var(--color-neutral)" }}>
                      Phone Number
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. +60123456789"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      className="w-full px-3 py-2 rounded-md border focus:outline-none"
                      style={{
                        background: "var(--color-paper-3)",
                        color: "var(--color-ink)",
                        borderColor: "var(--color-rule)",
                      }}
                    />
                  </div>

                  <div>
                    <label className="block font-medium mb-1" style={{ color: "var(--color-neutral)" }}>
                      Email Address
                    </label>
                    <input
                      type="email"
                      placeholder="user@umk.edu.my"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="w-full px-3 py-2 rounded-md border focus:outline-none"
                      style={{
                        background: "var(--color-paper-3)",
                        color: "var(--color-ink)",
                        borderColor: "var(--color-rule)",
                      }}
                    />
                  </div>
                </div>

                <div>
                  <label className="block font-medium mb-1" style={{ color: "var(--color-neutral)" }}>
                    Vehicle Type
                  </label>
                  <select
                    value={formData.vehicle_type}
                    onChange={(e) => setFormData({ ...formData, vehicle_type: e.target.value })}
                    className="w-full px-3 py-2 rounded-md border focus:outline-none"
                    style={{
                      background: "var(--color-paper-3)",
                      color: "var(--color-ink)",
                      borderColor: "var(--color-rule)",
                    }}
                  >
                    <option value="Car">Car</option>
                    <option value="Motorcycle">Motorcycle</option>
                    <option value="SUV">SUV</option>
                    <option value="Lorry">Lorry / Truck</option>
                    <option value="Official">Official Vehicle</option>
                  </select>
                </div>


                <div className="pt-3 flex items-center justify-end gap-3 border-t" style={{ borderColor: "var(--color-rule)" }}>
                  <button
                    type="button"
                    onClick={() => setIsAddModalOpen(false)}
                    className="px-4 py-2 font-medium rounded-md hover:bg-black/5 dark:hover:bg-white/5"
                    style={{ color: "var(--color-neutral)" }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-4 py-2 font-semibold text-white rounded-md shadow transition"
                    style={{ background: "var(--color-accent)" }}
                  >
                    {submitting ? "Saving..." : "Add Vehicle Permit"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: Delete Confirmation */}
        {deleteConfirmId && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-150">
            <div
              className="w-full max-w-md p-6 rounded-xl border shadow-2xl space-y-4"
              style={{
                background: "var(--color-paper-2)",
                borderColor: "var(--color-rule)",
              }}
            >
              <div className="flex items-center gap-3">
                <div className="p-3 rounded-lg bg-rose-500/10 text-rose-600">
                  <AlertTriangle size={24} />
                </div>
                <div>
                  <h3 className="text-base font-bold" style={{ color: "var(--color-ink)" }}>
                    Remove Vehicle Permit?
                  </h3>
                  <p className="text-xs text-neutral mt-0.5">
                    This action will permanently delete this vehicle permit from Supabase. Live ANPR will classify future passes as Unregistered.
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  onClick={() => setDeleteConfirmId(null)}
                  className="px-4 py-2 text-xs font-medium rounded-md hover:bg-black/5 dark:hover:bg-white/5 text-neutral"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleDelete(deleteConfirmId)}
                  className="px-4 py-2 text-xs font-semibold rounded-md bg-rose-600 hover:bg-rose-700 text-white shadow"
                >
                  Confirm Delete
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AdminGuard>
  );
}
