"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Upload, FileText, X, CheckCircle, AlertCircle } from "lucide-react";
import axios from "axios";
import { io, Socket } from "socket.io-client";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "http://localhost:5000";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [status, setStatus] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [jobId, setJobId] = useState<string>("");
  const [socket, setSocket] = useState<Socket | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  useEffect(() => {
    return () => {
      if (socket) {
        socket.disconnect();
      }
    };
  }, [socket]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (
        selectedFile.type === "application/pdf" ||
        selectedFile.type.startsWith("image/")
      ) {
        setFile(selectedFile);
        setError("");
      } else {
        setError("Please select a PDF or image file");
        setFile(null);
      }
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      if (
        droppedFile.type === "application/pdf" ||
        droppedFile.type.startsWith("image/")
      ) {
        setFile(droppedFile);
        setError("");
      } else {
        setError("Please select a PDF or image file");
        setFile(null);
      }
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError("");
    setStatus("Uploading file...");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await axios.post(`${API_URL}/api/upload`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      const newJobId = response.data.jobId;
      setJobId(newJobId);
      setUploading(false);
      setProcessing(true);
      setStatus("Processing document with AI...");

      const newSocket = io(WS_URL, {
        transports: ["websocket", "polling"],
      });

      newSocket.on("connect", () => {
        console.log("Connected to WebSocket");
      });

      newSocket.on("processing_status", (data: any) => {
        if (data.jobId === newJobId) {
          setStatus(data.message || "Processing...");

          if (data.status === "completed") {
            setProcessing(false);
            setStatus("Extraction completed successfully!");

            setTimeout(() => {
              if (data.orderId) {
                router.push(`/invoice/${data.orderId}`);
              } else {
                router.push("/");
              }
            }, 2000);
          } else if (data.status === "error") {
            setProcessing(false);
            setError(data.message || "An error occurred during processing");
          }
        }
      });

      newSocket.on("disconnect", () => {
        console.log("Disconnected from WebSocket");
      });

      setSocket(newSocket);
    } catch (err: any) {
      setUploading(false);
      setProcessing(false);
      setError(err.response?.data?.error || "Failed to upload file");
    }
  };

  const removeFile = () => {
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-3xl mx-auto">
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-gray-800 mb-2">
              Upload Invoice
            </h1>
            <p className="text-gray-600">
              Upload a PDF or image file to extract invoice data using AI
            </p>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-8">
            {!file && !processing && (
              <div
                onDrop={handleDrop}
                onDragOver={(e) => e.preventDefault()}
                className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-blue-500 transition-colors cursor-pointer"
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-700 mb-2">
                  Drag and drop your invoice here
                </h3>
                <p className="text-gray-500 mb-4">or click to browse</p>
                <p className="text-sm text-gray-400">
                  Supports PDF and image files (PNG, JPG, JPEG, GIF)
                </p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.png,.jpg,.jpeg,.gif"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </div>
            )}

            {file && !processing && (
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <FileText className="w-8 h-8 text-blue-600" />
                    <div>
                      <p className="font-medium text-gray-800">{file.name}</p>
                      <p className="text-sm text-gray-500">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={removeFile}
                    className="text-red-500 hover:text-red-700"
                  >
                    <X className="w-6 h-6" />
                  </button>
                </div>

                <button
                  onClick={handleUpload}
                  disabled={uploading}
                  className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg shadow-lg transition-colors flex items-center justify-center gap-2"
                >
                  {uploading ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="w-5 h-5" />
                      Upload and Process
                    </>
                  )}
                </button>
              </div>
            )}

            {processing && (
              <div className="text-center py-8">
                <div className="inline-block animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 border-t-transparent mb-4"></div>
                <p className="text-lg font-medium text-gray-700 mb-2">
                  {status}
                </p>
                <p className="text-sm text-gray-500">
                  This may take a few moments...
                </p>
              </div>
            )}

            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-red-800">Error</p>
                  <p className="text-sm text-red-600">{error}</p>
                </div>
              </div>
            )}

            {status && !error && !processing && (
              <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
                <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-green-800">Success</p>
                  <p className="text-sm text-green-600">{status}</p>
                </div>
              </div>
            )}
          </div>

          <div className="mt-8 bg-blue-50 rounded-lg p-6">
            <h3 className="font-semibold text-gray-800 mb-2">How it works:</h3>
            <ol className="list-decimal list-inside space-y-2 text-gray-600">
              <li>Upload your invoice document (PDF or image)</li>
              <li>Our AI extracts key information automatically</li>
              <li>Review and edit the extracted data</li>
              <li>Save to database for future reference</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
}
