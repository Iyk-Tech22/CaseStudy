"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { ArrowLeft, Save, Trash2, Plus, X } from "lucide-react";
import axios from "axios";
import { format } from "date-fns";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

interface OrderDetail {
  detailId?: number;
  productName: string;
  productCode: string;
  quantity: number;
  unitPrice: number;
  lineTotal: number;
  description: string;
}

interface Invoice {
  orderId: number;
  customerName: string;
  customerEmail: string;
  orderDate: string;
  invoiceNumber: string;
  totalAmount: number;
  taxAmount: number;
  shippingAddress: string;
  billingAddress: string;
  status: string;
  orderDetails: OrderDetail[];
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
    customerName: "",
    customerEmail: "",
    orderDate: "",
    invoiceNumber: "",
    totalAmount: 0,
    taxAmount: 0,
    shippingAddress: "",
    billingAddress: "",
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
        customerName: data.customerName || "",
        customerEmail: data.customerEmail || "",
        orderDate: data.orderDate || "",
        invoiceNumber: data.invoiceNumber || "",
        totalAmount: data.totalAmount || 0,
        taxAmount: data.taxAmount || 0,
        shippingAddress: data.shippingAddress || "",
        billingAddress: data.billingAddress || "",
        status: data.status || "",
      });
      setDetails(data.orderDetails || []);
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
        name === "totalAmount" || name === "taxAmount"
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

    if (field === "quantity" || field === "unitPrice") {
      updated[index].lineTotal =
        updated[index].quantity * updated[index].unitPrice;
    }

    setDetails(updated);

    const subtotal = updated.reduce((sum, d) => sum + d.lineTotal, 0);
    setFormData((prev) => ({
      ...prev,
      totalAmount: subtotal + prev.taxAmount,
    }));
  };

  const addDetail = () => {
    setDetails([
      ...details,
      {
        productName: "",
        productCode: "",
        quantity: 1,
        unitPrice: 0,
        lineTotal: 0,
        description: "",
      },
    ]);
  };

  const removeDetail = (index: number) => {
    const updated = details.filter((_, i) => i !== index);
    setDetails(updated);

    const subtotal = updated.reduce((sum, d) => sum + d.lineTotal, 0);
    setFormData((prev) => ({
      ...prev,
      totalAmount: subtotal + prev.taxAmount,
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    setError("");

    try {
      await axios.put(`${API_URL}/api/invoices/${invoice?.orderId}`, formData);

      await axios.put(
        `${API_URL}/api/invoices/${invoice?.orderId}/details`,
        details
      );

      setEditing(false);
      fetchInvoice(invoice!.orderId);
    } catch (err: any) {
      setError(err.response?.data?.error || "Failed to save invoice");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this invoice?")) return;

    try {
      await axios.delete(`${API_URL}/api/invoices/${invoice?.orderId}`);
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
                      fetchInvoice(invoice.orderId);
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
                    name="customerName"
                    value={formData.customerName}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
                  />
                ) : (
                  <p className="text-gray-900">{invoice.customerName}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Customer Email
                </label>
                {editing ? (
                  <input
                    type="email"
                    name="customerEmail"
                    value={formData.customerEmail}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
                  />
                ) : (
                  <p className="text-gray-900">
                    {invoice.customerEmail || "N/A"}
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
                    name="invoiceNumber"
                    value={formData.invoiceNumber}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
                  />
                ) : (
                  <p className="text-gray-900">{invoice.invoiceNumber}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Order Date
                </label>
                {editing ? (
                  <input
                    type="date"
                    name="orderDate"
                    value={formData.orderDate}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
                  />
                ) : (
                  <p className="text-gray-900">
                    {format(new Date(invoice.orderDate), "MMMM dd, yyyy")}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Shipping Address
                </label>
                {editing ? (
                  <textarea
                    name="shippingAddress"
                    value={formData.shippingAddress}
                    onChange={handleInputChange}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
                  />
                ) : (
                  <p className="text-gray-900 whitespace-pre-line">
                    {invoice.shippingAddress || "N/A"}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Billing Address
                </label>
                {editing ? (
                  <textarea
                    name="billingAddress"
                    value={formData.billingAddress}
                    onChange={handleInputChange}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
                  />
                ) : (
                  <p className="text-gray-900 whitespace-pre-line">
                    {invoice.billingAddress || "N/A"}
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
                    name="taxAmount"
                    value={formData.taxAmount}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
                  />
                ) : (
                  <p className="text-gray-900">
                    ${invoice.taxAmount.toFixed(2)}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Total Amount
                </label>
                <p className="text-2xl font-bold text-gray-900">
                  ${formData.totalAmount.toFixed(2)}
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
                            value={detail.productCode}
                            onChange={(e) =>
                              handleDetailChange(
                                index,
                                "productCode",
                                e.target.value
                              )
                            }
                            className="w-full px-2 py-1 border border-gray-300 rounded text-gray-900 bg-white"
                          />
                        ) : (
                          <span className="text-sm text-gray-900">
                            {detail.productCode || "N/A"}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {editing ? (
                          <input
                            type="text"
                            value={detail.productName}
                            onChange={(e) =>
                              handleDetailChange(
                                index,
                                "productName",
                                e.target.value
                              )
                            }
                            className="w-full px-2 py-1 border border-gray-300 rounded text-gray-900 bg-white"
                          />
                        ) : (
                          <span className="text-sm text-gray-900">
                            {detail.productName}
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
                            value={detail.unitPrice}
                            onChange={(e) =>
                              handleDetailChange(
                                index,
                                "unitPrice",
                                parseFloat(e.target.value) || 0
                              )
                            }
                            className="w-full px-2 py-1 border border-gray-300 rounded text-gray-900 bg-white"
                          />
                        ) : (
                          <span className="text-sm text-gray-900">
                            ${detail.unitPrice.toFixed(2)}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-sm font-semibold text-gray-900">
                          ${detail.lineTotal.toFixed(2)}
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
