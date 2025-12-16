"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { ArrowLeft, Save, Trash2, Plus, X } from "lucide-react";
import axios from "axios";
import { format } from "date-fns";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

interface OrderDetail {
  detail_id?: number;
  product_name: string;
  product_code: string;
  quantity: number;
  unit_price: number;
  line_total: number;
  description: string;
}

interface Invoice {
  order_id: number;
  customer_name: string;
  customer_email: string;
  order_date: string;
  invoice_number: string;
  total_amount: number;
  tax_amount: number;
  shipping_address: string;
  billing_address: string;
  status: string;
  order_details: OrderDetail[];
}

export default function InvoiceDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState(false);
  const [error, setError] = useState("");

  const [formData, setFormData] = useState({
    customer_name: "",
    customer_email: "",
    order_date: "",
    invoice_number: "",
    total_amount: 0,
    tax_amount: 0,
    shipping_address: "",
    billing_address: "",
    status: "",
  });

  const [details, setDetails] = useState<OrderDetail[]>([]);

  useEffect(() => {
    if (params.id) {
      fetchInvoice(Number(params.id));
    }
  }, [params.id]);

  const fetchInvoice = async (id: number) => {
    try {
      const response = await axios.get(`${API_URL}/api/invoices/${id}`);
      const data = response.data;
      setInvoice(data);
      setFormData({
        customer_name: data.customer_name || "",
        customer_email: data.customer_email || "",
        order_date: data.order_date || "",
        invoice_number: data.invoice_number || "",
        total_amount: data.total_amount || 0,
        tax_amount: data.tax_amount || 0,
        shipping_address: data.shipping_address || "",
        billing_address: data.billing_address || "",
        status: data.status || "",
      });
      setDetails(data.order_details || []);
    } catch (err: any) {
      setError(err.response?.data?.error || "Failed to load invoice");
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]:
        name === "total_amount" || name === "tax_amount"
          ? parseFloat(value) || 0
          : value,
    }));
  };

  const handleDetailChange = (
    index: number,
    field: keyof OrderDetail,
    value: any
  ) => {
    const updated = [...details];
    updated[index] = { ...updated[index], [field]: value };

    if (field === "quantity" || field === "unit_price") {
      updated[index].line_total =
        updated[index].quantity * updated[index].unit_price;
    }

    setDetails(updated);

    const subtotal = updated.reduce((sum, d) => sum + d.line_total, 0);
    setFormData((prev) => ({
      ...prev,
      total_amount: subtotal + prev.tax_amount,
    }));
  };

  const addDetail = () => {
    setDetails([
      ...details,
      {
        product_name: "",
        product_code: "",
        quantity: 1,
        unit_price: 0,
        line_total: 0,
        description: "",
      },
    ]);
  };

  const removeDetail = (index: number) => {
    const updated = details.filter((_, i) => i !== index);
    setDetails(updated);

    const subtotal = updated.reduce((sum, d) => sum + d.line_total, 0);
    setFormData((prev) => ({
      ...prev,
      total_amount: subtotal + prev.tax_amount,
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    setError("");

    try {
      await axios.put(`${API_URL}/api/invoices/${invoice?.order_id}`, formData);

      await axios.put(
        `${API_URL}/api/invoices/${invoice?.order_id}/details`,
        details
      );

      setEditing(false);
      fetchInvoice(invoice!.order_id);
    } catch (err: any) {
      setError(err.response?.data?.error || "Failed to save invoice");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this invoice?")) return;

    try {
      await axios.delete(`${API_URL}/api/invoices/${invoice?.order_id}`);
      router.push("/");
    } catch (err: any) {
      setError(err.response?.data?.error || "Failed to delete invoice");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading invoice...</p>
        </div>
      </div>
    );
  }

  if (!invoice) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 mb-4">Invoice not found</p>
          <Link href="/" className="text-blue-600 hover:text-blue-800">
            Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          <div className="mb-6 flex items-center justify-between">
            <Link
              href="/"
              className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-800"
            >
              <ArrowLeft className="w-5 h-5" />
              Back to Dashboard
            </Link>
            <div className="flex gap-2">
              {editing ? (
                <>
                  <button
                    onClick={() => {
                      setEditing(false);
                      fetchInvoice(invoice.order_id);
                    }}
                    className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:bg-gray-400"
                  >
                    <Save className="w-4 h-4" />
                    {saving ? "Saving..." : "Save"}
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={handleDelete}
                    className="inline-flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg"
                  >
                    <Trash2 className="w-4 h-4" />
                    Delete
                  </button>
                  <button
                    onClick={() => setEditing(true)}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
                  >
                    Edit
                  </button>
                </>
              )}
            </div>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
              {error}
            </div>
          )}

          <div className="bg-white rounded-lg shadow-lg p-8 mb-6">
            <h1 className="text-3xl font-bold text-gray-800 mb-6">
              Invoice Details
            </h1>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Customer Name
                </label>
                {editing ? (
                  <input
                    type="text"
                    name="customer_name"
                    value={formData.customer_name}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
                  />
                ) : (
                  <p className="text-gray-900">{invoice.customer_name}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Customer Email
                </label>
                {editing ? (
                  <input
                    type="email"
                    name="customer_email"
                    value={formData.customer_email}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
                  />
                ) : (
                  <p className="text-gray-900">
                    {invoice.customer_email || "N/A"}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Invoice Number
                </label>
                {editing ? (
                  <input
                    type="text"
                    name="invoice_number"
                    value={formData.invoice_number}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
                  />
                ) : (
                  <p className="text-gray-900">{invoice.invoice_number}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Order Date
                </label>
                {editing ? (
                  <input
                    type="date"
                    name="order_date"
                    value={formData.order_date}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
                  />
                ) : (
                  <p className="text-gray-900">
                    {format(new Date(invoice.order_date), "MMMM dd, yyyy")}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Shipping Address
                </label>
                {editing ? (
                  <textarea
                    name="shipping_address"
                    value={formData.shipping_address}
                    onChange={handleInputChange}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
                  />
                ) : (
                  <p className="text-gray-900 whitespace-pre-line">
                    {invoice.shipping_address || "N/A"}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Billing Address
                </label>
                {editing ? (
                  <textarea
                    name="billing_address"
                    value={formData.billing_address}
                    onChange={handleInputChange}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
                  />
                ) : (
                  <p className="text-gray-900 whitespace-pre-line">
                    {invoice.billing_address || "N/A"}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tax Amount
                </label>
                {editing ? (
                  <input
                    type="number"
                    step="0.01"
                    name="tax_amount"
                    value={formData.tax_amount}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
                  />
                ) : (
                  <p className="text-gray-900">
                    ${invoice.tax_amount.toFixed(2)}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Total Amount
                </label>
                <p className="text-2xl font-bold text-gray-900">
                  ${formData.total_amount.toFixed(2)}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-800">
                Order Details
              </h2>
              {editing && (
                <button
                  onClick={addDetail}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg"
                >
                  <Plus className="w-4 h-4" />
                  Add Item
                </button>
              )}
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Product Code
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Product Name
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Quantity
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Unit Price
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Line Total
                    </th>
                    {editing && (
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Actions
                      </th>
                    )}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {details.map((detail, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        {editing ? (
                          <input
                            type="text"
                            value={detail.product_code}
                            onChange={(e) =>
                              handleDetailChange(
                                index,
                                "product_code",
                                e.target.value
                              )
                            }
                            className="w-full px-2 py-1 border border-gray-300 rounded text-gray-900 bg-white"
                          />
                        ) : (
                          <span className="text-sm text-gray-900">
                            {detail.product_code || "N/A"}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {editing ? (
                          <input
                            type="text"
                            value={detail.product_name}
                            onChange={(e) =>
                              handleDetailChange(
                                index,
                                "product_name",
                                e.target.value
                              )
                            }
                            className="w-full px-2 py-1 border border-gray-300 rounded text-gray-900 bg-white"
                          />
                        ) : (
                          <span className="text-sm text-gray-900">
                            {detail.product_name}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {editing ? (
                          <input
                            type="number"
                            value={detail.quantity}
                            onChange={(e) =>
                              handleDetailChange(
                                index,
                                "quantity",
                                parseInt(e.target.value) || 0
                              )
                            }
                            className="w-full px-2 py-1 border border-gray-300 rounded text-gray-900 bg-white"
                          />
                        ) : (
                          <span className="text-sm text-gray-900">
                            {detail.quantity}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {editing ? (
                          <input
                            type="number"
                            step="0.01"
                            value={detail.unit_price}
                            onChange={(e) =>
                              handleDetailChange(
                                index,
                                "unit_price",
                                parseFloat(e.target.value) || 0
                              )
                            }
                            className="w-full px-2 py-1 border border-gray-300 rounded text-gray-900 bg-white"
                          />
                        ) : (
                          <span className="text-sm text-gray-900">
                            ${detail.unit_price.toFixed(2)}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-sm font-semibold text-gray-900">
                          ${detail.line_total.toFixed(2)}
                        </span>
                      </td>
                      {editing && (
                        <td className="px-4 py-3">
                          <button
                            onClick={() => removeDetail(index)}
                            className="text-red-600 hover:text-red-800"
                          >
                            <X className="w-5 h-5" />
                          </button>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
