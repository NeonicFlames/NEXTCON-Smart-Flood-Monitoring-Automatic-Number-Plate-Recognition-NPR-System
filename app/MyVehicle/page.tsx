"use client";

import { useState } from "react";
import {
  checkVehiclePermit,
  addRegisteredVehicle,
  NewVehicleInput,
} from "@/lib/queries/vehicles";
import {
  Car,
  Search,
  CheckCircle2,
  AlertCircle,
  PlusCircle,
  ShieldCheck,
  Building2,
  Clock,
  Sparkles
} from "lucide-react";

interface PermitResult {
  plate_number: string;
  owner_name: string;
  vehicle_type?: string;
  zone?: string;
  is_active: boolean;
  created_at: string;
}

export default function MyVehiclePage() {
  // Search state
  const [searchPlate, setSearchPlate] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchResult, setSearchResult] = useState<PermitResult | null | undefined>(undefined);

  // Registration request state
  const [showRequestForm, setShowRequestForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState(false);

  const [formData, setFormData] = useState<NewVehicleInput>({
    plate_number: "",
    owner_name: "",
    phone: "",
    email: "",
    vehicle_type: "Car",
    zone: "Zone A",
  });

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchPlate.trim()) return;

    setSearching(true);
    setSearchResult(undefined);
    try {
      const res = await checkVehiclePermit(searchPlate);
      setSearchResult(res as PermitResult | null);
    } catch (err) {
      console.error("Permit search error:", err);
      setSearchResult(null);
    } finally {
      setSearching(false);
    }
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.plate_number.trim() || !formData.owner_name.trim()) return;

    setSubmitting(true);
    try {
      await addRegisteredVehicle({
        ...formData,
        is_active: false, // Submitted as Pending Approval for Admin review
      });

      setSuccessMessage(true);
      setShowRequestForm(false);
      setFormData({
        plate_number: "",
        owner_name: "",
        phone: "",
        email: "",
        vehicle_type: "Car",
        zone: "Zone A",
      });
    } catch (err) {
      console.error("Self registration error:", err);
      alert("Failed to submit vehicle registration. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
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
            <h1
              className="text-xl font-semibold tracking-tight"
              style={{
                color: "var(--color-ink)",
                fontFamily: "var(--font-display)",
                letterSpacing: "-0.02em",
              }}
            >
              Vehicle Permit Lookup &amp; Registration
            </h1>
            <p className="mt-0.5 text-sm" style={{ color: "var(--color-neutral)" }}>
              Check your campus gate entry clearance or apply for vehicle registration
            </p>
          </div>
        </div>

        <button
          onClick={() => {
            setShowRequestForm(!showRequestForm);
            setSuccessMessage(false);
          }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-md text-xs font-semibold shadow-sm transition self-start sm:self-auto"
          style={{
            background: "var(--color-accent)",
            color: "#ffffff",
          }}
        >
          <PlusCircle size={16} />
          <span>{showRequestForm ? "Close Form" : "Register My Vehicle"}</span>
        </button>
      </div>

      {/* Success Notification */}
      {successMessage && (
        <div
          className="p-4 rounded-xl border flex items-center gap-3 animate-in fade-in"
          style={{
            background: "var(--color-warn-subtle)",
            borderColor: "oklch(78% 0.18 85 / 0.3)",
            color: "var(--color-warn)",
          }}
        >
          <Clock size={20} className="shrink-0" />
          <div className="text-xs">
            <p className="font-bold text-sm">Vehicle Permit Request Submitted!</p>
            <p className="mt-0.5">
              Your permit request is currently <strong>Pending Admin Approval</strong>. Once campus security reviews and approves your request on the Admin Dashboard, your vehicle will gain gate clearance.
            </p>
          </div>
        </div>
      )}


      {/* Vehicle Permit Verification Card */}
      <section
        className="p-6 rounded-2xl border space-y-6 shadow-sm"
        style={{
          background: "var(--color-paper-2)",
          borderColor: "var(--color-rule)",
        }}
      >
        <div className="flex items-center gap-2">
          <ShieldCheck size={20} style={{ color: "var(--color-accent)" }} />
          <h2
            className="text-base font-semibold"
            style={{ color: "var(--color-ink)", fontFamily: "var(--font-display)" }}
          >
            Check Vehicle Gate Clearance
          </h2>
        </div>

        <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search
              size={18}
              className="absolute left-3.5 top-1/2 -translate-y-1/2"
              style={{ color: "var(--color-muted)" }}
            />
            <input
              type="text"
              required
              placeholder="Enter your Plate Number (e.g. WYY 8888)"
              value={searchPlate}
              onChange={(e) => setSearchPlate(e.target.value.toUpperCase())}
              className="w-full pl-10 pr-4 py-3 rounded-lg text-base border focus:outline-none uppercase font-bold tracking-wider"
              style={{
                background: "var(--color-paper-3)",
                color: "var(--color-accent)",
                borderColor: "var(--color-rule)",
                fontFamily: "var(--font-outlier)",
              }}
            />
          </div>
          <button
            type="submit"
            disabled={searching}
            className="px-6 py-3 rounded-lg text-sm font-semibold shadow transition flex items-center justify-center gap-2 shrink-0"
            style={{
              background: "var(--color-accent)",
              color: "#ffffff",
            }}
          >
            {searching ? (
              <span>Checking...</span>
            ) : (
              <>
                <Search size={16} />
                <span>Verify Permit</span>
              </>
            )}
          </button>
        </form>

        {/* Search Results Display */}
        {searchResult !== undefined && (
          <div className="pt-4 border-t" style={{ borderColor: "var(--color-rule)" }}>
            {searchResult === null ? (
              <div
                className="p-4 rounded-xl border flex items-center gap-3 text-xs"
                style={{
                  background: "var(--color-warn-subtle)",
                  borderColor: "oklch(78% 0.18 85 / 0.3)",
                  color: "var(--color-warn)",
                }}
              >
                <AlertCircle size={20} className="shrink-0" />
                <div>
                  <p className="font-bold text-sm">No Permit Found for "{searchPlate}"</p>
                  <p className="mt-0.5">
                    This plate is currently unregistered in the UMK ANPR system. You can click <strong>Register My Vehicle</strong> above to submit your vehicle for clearance.
                  </p>
                </div>
              </div>
            ) : (
              <div
                className="p-5 rounded-xl border space-y-4"
                style={{
                  background: "var(--color-paper-3)",
                  borderColor: "var(--color-rule)",
                }}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-neutral">
                      PERMIT VERIFICATION MATCH
                    </span>
                    <h3
                      className="text-3xl font-extrabold tracking-wider mt-1"
                      style={{
                        color: "var(--color-accent)",
                        fontFamily: "var(--font-outlier)",
                      }}
                    >
                      {searchResult.plate_number}
                    </h3>
                  </div>

                  <span
                    className="inline-flex items-center gap-2 text-xs font-bold px-3.5 py-1.5 rounded-full self-start sm:self-auto"
                    style={{
                      background: searchResult.is_active
                        ? "var(--color-safe-subtle)"
                        : "var(--color-warn-subtle)",
                      color: searchResult.is_active
                        ? "var(--color-safe)"
                        : "var(--color-warn)",
                      border: `1px solid ${
                        searchResult.is_active
                          ? "oklch(70% 0.18 145 / 0.3)"
                          : "oklch(78% 0.18 85 / 0.3)"
                      }`,
                    }}
                  >
                    <CheckCircle2 size={16} />
                    {searchResult.is_active ? "Authorized for Campus Gate" : "Suspended Permit"}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-4 pt-3 border-t text-xs" style={{ borderColor: "var(--color-rule)" }}>
                  <div>
                    <p className="text-neutral font-medium">Registered Owner</p>
                    <p className="font-semibold text-ink text-sm mt-0.5">{searchResult.owner_name}</p>
                  </div>

                  <div>
                    <p className="text-neutral font-medium">Vehicle Category</p>
                    <p className="font-semibold text-ink text-sm mt-0.5">{searchResult.vehicle_type || "Car"}</p>
                  </div>
                </div>

              </div>
            )}
          </div>
        )}
      </section>

      {/* Registration Request Form */}
      {showRequestForm && (
        <section
          className="p-6 rounded-2xl border space-y-6 shadow-sm animate-in fade-in slide-in-from-top-4 duration-200"
          style={{
            background: "var(--color-paper-2)",
            borderColor: "var(--color-rule)",
          }}
        >
          <div className="flex items-center gap-2">
            <Sparkles size={20} style={{ color: "var(--color-accent)" }} />
            <h2
              className="text-base font-semibold"
              style={{ color: "var(--color-ink)", fontFamily: "var(--font-display)" }}
            >
              Submit Vehicle Registration Request
            </h2>
          </div>

          <form onSubmit={handleRegisterSubmit} className="space-y-4 text-xs">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
                  className="w-full px-3.5 py-2.5 rounded-md border focus:outline-none uppercase font-bold tracking-wider text-sm"
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
                  Full Owner Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="Your full official name"
                  value={formData.owner_name}
                  onChange={(e) => setFormData({ ...formData, owner_name: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-md border focus:outline-none text-sm"
                  style={{
                    background: "var(--color-paper-3)",
                    color: "var(--color-ink)",
                    borderColor: "var(--color-rule)",
                  }}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block font-medium mb-1" style={{ color: "var(--color-neutral)" }}>
                  Phone Number
                </label>
                <input
                  type="text"
                  placeholder="+60123456789"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-md border focus:outline-none"
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
                  placeholder="name@umk.edu.my"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-md border focus:outline-none"
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
                className="w-full px-3.5 py-2.5 rounded-md border focus:outline-none"
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
              </select>
            </div>


            <div className="pt-4 flex items-center justify-end gap-3 border-t" style={{ borderColor: "var(--color-rule)" }}>
              <button
                type="button"
                onClick={() => setShowRequestForm(false)}
                className="px-4 py-2 font-medium rounded-md text-neutral hover:bg-black/5 dark:hover:bg-white/5"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="px-5 py-2.5 font-semibold text-white rounded-md shadow transition"
                style={{ background: "var(--color-accent)" }}
              >
                {submitting ? "Submitting..." : "Submit Registration Request"}
              </button>
            </div>
          </form>
        </section>
      )}
    </div>
  );
}
