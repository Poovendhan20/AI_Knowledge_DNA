import {
  useEffect,
  useRef,
  useState,
} from "react";
import { useNavigate } from "react-router-dom";
import {
  FaPlus,
  FaBook,
  FaTrash,
  FaUpload,
  FaFilePdf,
  FaFilePowerpoint,
  FaFileWord,
  FaImage,
  FaEye,
  FaDownload,
  FaChevronRight,
  FaTimes,
  FaCheckCircle,
  FaFileAlt,
} from "react-icons/fa";
import {
  createSubject,
  getSubjects,
  deleteSubject,
  uploadMultipleDocuments,
  getSubjectDocuments,
} from "../../services/subjectApi";
import {
  getFileBlob,
} from "../../services/api";
import "./SubjectManager.css";
function SubjectManager() {
  const navigate = useNavigate();
  // =====================================================
  // SUBJECT STATE
  // =====================================================
  const [
    subjects,
    setSubjects,
  ] = useState([]);
  const [
    selectedSubject,
    setSelectedSubject,
  ] = useState(null);
  const [
    subjectName,
    setSubjectName,
  ] = useState("");
  const [
    description,
    setDescription,
  ] = useState("");
  // =====================================================
  // DOCUMENT STATE
  // =====================================================
  const [
    documents,
    setDocuments,
  ] = useState([]);
  const [
    documentsLoading,
    setDocumentsLoading,
  ] = useState(false);
  // =====================================================
  // UPLOAD STATE
  // =====================================================
  const [
    selectedFiles,
    setSelectedFiles,
  ] = useState([]);
  const [
    isDragging,
    setIsDragging,
  ] = useState(false);
  const [
    uploading,
    setUploading,
  ] = useState(false);
  const [
    loading,
    setLoading,
  ] = useState(false);
  const [
    message,
    setMessage,
  ] = useState("");
  const [
    messageType,
    setMessageType,
  ] = useState("");
  const fileInputRef = useRef(null);

  const showMessage = (
    text,
    type = "success"
  ) => {
    setMessage(text);
    setMessageType(type);
    window.setTimeout(() => {
      setMessage("");
      setMessageType("");
    }, 4000);
  };
  // =====================================================
  // LOAD SUBJECTS
  // =====================================================
  const loadSubjects = async (
    keepSelectedId = null
  ) => {
    try {
      setLoading(true);
      const result =
        await getSubjects();
      if (result?.success) {
        const nextSubjects =
          result.subjects || [];
        setSubjects(nextSubjects);
        if (keepSelectedId) {
          const existing =
            nextSubjects.find(
              (subject) =>
                String(subject.id) ===
                String(keepSelectedId)
            );
          if (existing) {
            setSelectedSubject(existing);
          }
        } else {
          setSelectedSubject((current) => {
            if (current) {
              const matched = nextSubjects.find(
                (subject) => String(subject.id) === String(current.id)
              );
              if (matched) return matched;
            }
            return nextSubjects.length > 0 ? nextSubjects[0] : null;
          });
        }
      }
    } catch (error) {
      console.error(
        "Unable to load subjects:",
        error
      );
      showMessage(
        "Unable to load subjects.",
        "error"
      );
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    loadSubjects();
  }, []);
  // =====================================================
  // LOAD SUBJECT DOCUMENTS
  // =====================================================
  const loadSubjectDocuments = async (
    subjectId,
    {
      preserveCurrentDocuments = false,
    } = {}
  ) => {
    if (!subjectId) {
      if (!preserveCurrentDocuments) {
        setDocuments([]);
      }
      return;
    }
    try {
      setDocumentsLoading(true);
      const result =
        await getSubjectDocuments(
          subjectId
        );
      if (result?.success) {
        setDocuments(
          result.documents || []
        );
      } else if (!preserveCurrentDocuments) {
        setDocuments([]);
      }
    } catch (error) {
      console.error(
        "Unable to load subject documents:",
        error
      );
      if (!preserveCurrentDocuments) {
        setDocuments([]);
      }
      showMessage(
        "Unable to load study materials.",
        "error"
      );
    } finally {
      setDocumentsLoading(false);
    }
  };
  // =====================================================
  // SELECT SUBJECT
  // =====================================================
  useEffect(() => {
    if (!selectedSubject?.id) {
      setDocuments([]);
      return;
    }
    loadSubjectDocuments(
      selectedSubject.id
    );
  }, [
    selectedSubject?.id,
  ]);
  // =====================================================
  // CREATE SUBJECT
  // =====================================================
  const handleCreateSubject = async (
    event
  ) => {
    event.preventDefault();
    if (!subjectName.trim()) {
      showMessage(
        "Enter a subject name.",
        "error"
      );
      return;
    }
    try {
      setLoading(true);
      const result =
        await createSubject(
          subjectName.trim(),
          description.trim()
        );
      if (result?.success) {
        const newSubject =
          result.subject;
        setSubjectName("");
        setDescription("");
        await loadSubjects(
          newSubject?.id
        );
        if (newSubject) {
          setSelectedSubject(
            newSubject
          );
          setDocuments([]);
        }
        showMessage(
          "Subject created successfully.",
          "success"
        );
      } else {
        showMessage(
          result?.message ||
          "Unable to create subject.",
          "error"
        );
      }
    } catch (error) {
      console.error(
        "Create subject error:",
        error
      );
      showMessage(
        error?.response?.data?.message ||
        "Unable to create subject.",
        "error"
      );
    } finally {
      setLoading(false);
    }
  };
  // =====================================================
  // DELETE SUBJECT
  // =====================================================
  const handleDeleteSubject = async (
    subjectId
  ) => {
    const confirmed =
      window.confirm(
        "Delete this subject? The subject will be removed from your study organization."
      );
    if (!confirmed) {
      return;
    }
    try {
      setLoading(true);
      await deleteSubject(
        subjectId
      );
      if (
        String(selectedSubject?.id) ===
        String(subjectId)
      ) {
        setSelectedSubject(null);
        setDocuments([]);
      }
      await loadSubjects();
      showMessage(
        "Subject deleted successfully.",
        "success"
      );
    } catch (error) {
      console.error(
        "Delete subject error:",
        error
      );
      showMessage(
        error?.response?.data?.message ||
        "Unable to delete subject.",
        "error"
      );
    } finally {
      setLoading(false);
    }
  };
  // =====================================================
  // FILE SELECT
  // =====================================================
  const handleFileChange = (
    event
  ) => {
    const files =
      Array.from(
        event.target.files || []
      );
    setSelectedFiles(
      files
    );
  };
  // =====================================================
  // UPLOAD
  // =====================================================
  const handleUpload = async () => {
    if (!selectedSubject) {
      showMessage(
        "Select a subject first.",
        "error"
      );
      return;
    }
    if (
      selectedFiles.length === 0
    ) {
      showMessage(
        "Select at least one file.",
        "error"
      );
      return;
    }
    try {
      const subjectId = selectedSubject.id;

      setUploading(true);
      setMessage("");
      const result =
        await uploadMultipleDocuments(
          subjectId,
          selectedFiles
        );
      if (result?.success) {
        const uploadedDocuments =
          result.documents || [];
        const uploadedIds = new Set(
          uploadedDocuments
            .map((document) => document?.id)
            .filter(Boolean)
        );

        setDocuments((currentDocuments) => [
          ...currentDocuments.filter(
            (document) =>
              !uploadedIds.has(document?.id)
          ),
          ...uploadedDocuments,
        ]);
        setSelectedFiles([]);
        if (fileInputRef.current) {
          fileInputRef.current.value =
            "";
        }
        await loadSubjectDocuments(
          subjectId,
          {
            preserveCurrentDocuments: true,
          }
        );
        await loadSubjects(
          subjectId
        );

        const failedFiles = result.errors || [];
        const failedMessage =
          failedFiles.length > 0
            ? ` ${failedFiles.length} file(s) could not be uploaded.`
            : "";

        showMessage(
          `${
            result.message ||
            "Study materials uploaded successfully."
          }${failedMessage}`,
          "success"
        );
      } else {
        showMessage(
          result?.message ||
          "Upload failed.",
          "error"
        );
      }
    } catch (error) {
      console.error(
        "Upload error:",
        error
      );
      showMessage(
        error?.response?.data?.message ||
        "Upload failed.",
        "error"
      );
    } finally {
      setUploading(false);
    }
  };
  // =====================================================
  // FILE ICON
  // =====================================================
  const getFileIcon = (
    type
  ) => {
    const extension =
      String(type || "")
        .toLowerCase()
        .replace(".", "");
    if (
      extension === "pdf"
    ) {
      return <FaFilePdf />;
    }
    if (
      extension === "pptx" ||
      extension === "ppt"
    ) {
      return (
        <FaFilePowerpoint />
      );
    }
    if (
      extension === "docx" ||
      extension === "doc"
    ) {
      return (
        <FaFileWord />
      );
    }
    if (
      [
        "png",
        "jpg",
        "jpeg",
        "webp",
      ].includes(extension)
    ) {
      return <FaImage />;
    }
    return <FaFileAlt />;
  };
  // =====================================================
  // DOCUMENT NAME
  // =====================================================
  const getDocumentName = (
    document
  ) => {
    return (
      document?.original_name ||
      document?.name ||
      document?.filename ||
      "Study Material"
    );
  };
  // =====================================================
  // DOCUMENT TYPE
  // =====================================================
  const getDocumentType = (
    document
  ) => {
    const type =
      document?.type ||
      getDocumentName(document)
        .split(".")
        .pop();
    return String(
      type || "file"
    ).toUpperCase();
  };
  // =====================================================
  // FORMAT DATE
  // =====================================================
  const formatDate = (
    document
  ) => {
    const date =
      document?.created_at ||
      document?.uploaded_at ||
      document?.upload_date;
    if (!date) {
      return "";
    }
    try {
      return new Date(
        date
      ).toLocaleDateString(
        "en-IN",
        {
          day: "2-digit",
          month: "short",
          year: "numeric",
        }
      );
    } catch {
      return "";
    }
  };
  // =====================================================
  // OPEN DOCUMENT
  // =====================================================
  const openDocument = (
    document
  ) => {
    if (!document?.id) {
      showMessage(
        "Document ID is unavailable.",
        "error"
      );
      return;
    }
    navigate(`/document/${document.id}`);
  };
  // =====================================================
  // DOWNLOAD DOCUMENT
  // =====================================================
  const downloadDocument = async (
    document
  ) => {
    if (!document?.stored_name) {
      showMessage(
        "File information is unavailable.",
        "error"
      );
      return;
    }
    try {
      const blob =
        await getFileBlob(
          document.stored_name
        );
      const url =
        URL.createObjectURL(
          blob
        );
      const link =
        window.document.createElement(
          "a"
        );
      link.href = url;
      link.download =
        getDocumentName(
          document
        );
      window.document.body.appendChild(
        link
      );
      link.click();
      link.remove();
      URL.revokeObjectURL(
        url
      );
    } catch (error) {
      console.error(
        "Download error:",
        error
      );
      showMessage(
        "Unable to download this file.",
        "error"
      );
    }
  };
  // =====================================================
  // DRAG & DROP HANDLERS
  // =====================================================
  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const dropped = Array.from(e.dataTransfer?.files || []);
    if (dropped.length > 0) {
      setSelectedFiles((current) => [...current, ...dropped]);
    }
  };

  // =====================================================
  // EMPTY STATE
  // =====================================================
  const renderDocuments = () => {
    if (documentsLoading) {
      return (
        <div className="sdna-documents-loading">
          <div className="sdna-spinner" />
          <span>
            Loading study materials...
          </span>
        </div>
      );
    }
    if (
      documents.length === 0
    ) {
      return (
        <div
          className={`sdna-empty-documents ${isDragging ? "dragging" : ""}`}
          onClick={() => fileInputRef.current?.click()}
        >
          <div className="sdna-empty-icon">
            <FaUpload />
          </div>
          <h4>
            No study materials yet
          </h4>
          <p>
            Drag and drop PDFs, PPTX, DOCX or images here, or click to browse.
          </p>
          <button
            type="button"
            className="sdna-secondary-button"
            onClick={(e) => {
              e.stopPropagation();
              fileInputRef.current?.click();
            }}
          >
            <FaUpload />
            Browse Files
          </button>
        </div>
      );
    }
    return (
      <div className="sdna-document-list">
        {documents.map(
          (document) => {
            const name =
              getDocumentName(
                document
              );
            const type =
              getDocumentType(
                document
              );
            const date =
              formatDate(
                document
              );
            return (
              <div
                className="sdna-document-card"
                key={document.id}
              >
                <div className="sdna-document-icon">
                  {getFileIcon(
                    document.type
                  )}
                </div>
                <div className="sdna-document-info">
                  <div
                    className="sdna-document-name"
                    title={name}
                  >
                    {name}
                  </div>
                  <div className="sdna-document-meta">
                    <span>
                      {type}
                    </span>
                    {document.page_count ? (
                      <>
                        <span>
                          •
                        </span>
                        <span>
                          {document.page_count}{" "}
                          {Number(
                            document.page_count
                          ) === 1
                            ? "page"
                            : "pages"}
                        </span>
                      </>
                    ) : null}
                    {date ? (
                      <>
                        <span>
                          •
                        </span>
                        <span>
                          {date}
                        </span>
                      </>
                    ) : null}
                  </div>
                </div>
                <div className="sdna-document-actions">
                  <button
                    type="button"
                    className="sdna-view-button"
                    onClick={() =>
                      openDocument(
                        document
                      )
                    }
                    title="Open document"
                  >
                    <FaEye />
                    <span>
                      View
                    </span>
                  </button>
                  <button
                    type="button"
                    className="sdna-download-button"
                    onClick={() =>
                      downloadDocument(
                        document
                      )
                    }
                    title="Download document"
                  >
                    <FaDownload />
                    <span>
                      Download
                    </span>
                  </button>
                </div>
              </div>
            );
          }
        )}
      </div>
    );
  };
  // =====================================================
  // RENDER
  // =====================================================
  return (
    <section className="sdna-subject-manager">
      {/* =================================================*
*&#xA0;         HEADER*
*&#xA0;     ================================================= */}
      <div className="sdna-page-header">
        <div>
          <span className="sdna-eyebrow">
            ORGANIZE YOUR LEARNING
          </span>
          <h2>
            My Subjects
          </h2>
          <p>
            Organize your study materials
            by subject.
          </p>
        </div>
      </div>
      {/* =================================================*
*&#xA0;         SUBJECT LAYOUT*
*&#xA0;     ================================================= */}
      <div className="sdna-subject-layout">
        {/* =================================================*
*&#xA0;           CREATE SUBJECT*
*&#xA0;       ================================================= */}
        <aside className="sdna-sidebar">
          <div className="sdna-sidebar-header">
            <div className="sdna-sidebar-icon">
              <FaBook />
            </div>
            <div>
              <h3>
                My Subjects
              </h3>
              <span>
                {subjects.length}{" "}
                {subjects.length === 1
                  ? "subject"
                  : "subjects"}
              </span>
            </div>
          </div>
          <form
            className="sdna-create-form"
            onSubmit={
              handleCreateSubject
            }
          >
            <div className="sdna-create-title">
              <FaPlus />
              Create Subject
            </div>
            <input
              type="text"
              placeholder="Subject name"
              value={subjectName}
              onChange={(event) =>
                setSubjectName(
                  event.target.value
                )
              }
            />
            <textarea
              placeholder="Description (optional)"
              value={description}
              onChange={(event) =>
                setDescription(
                  event.target.value
                )
              }
              rows={3}
            />
            <button
              type="submit"
              className="sdna-primary-button"
              disabled={loading}
            >
              <FaPlus />
              {loading
                ? "Creating..."
                : "Create Subject"}
            </button>
          </form>
          {/* SUBJECT LIST */}
          <div className="sdna-subject-list">
            {subjects.length === 0 ? (
              <div className="sdna-empty-subjects">
                <FaBook />
                <span>
                  No subjects yet.
                </span>
              </div>
            ) : (
              subjects.map(
                (subject) => {
                  const active =
                    String(
                      selectedSubject?.id
                    ) ===
                    String(
                      subject.id
                    );
                  return (
                    <button
                      type="button"
                      key={subject.id}
                      className={
                        active
                          ? "sdna-subject-item active"
                          : "sdna-subject-item"
                      }
                      onClick={() =>
                        setSelectedSubject(
                          subject
                        )
                      }
                    >
                      <div className="sdna-subject-icon">
                        <FaBook />
                      </div>
                      <div className="sdna-subject-info">
                        <strong>
                          {subject.name}
                        </strong>
                        <span>
                          {subject.document_count || 0}{" "}
                          {Number(
                            subject.document_count || 0
                          ) === 1
                            ? "material"
                            : "materials"}
                          {" • "}
                          {subject.topic_count || 0}{" "}
                          topics
                        </span>
                      </div>
                      <FaChevronRight />
                    </button>
                  );
                }
              )
            )}
          </div>
        </aside>
        {/* =================================================*
*&#xA0;           MAIN CONTENT*
*&#xA0;       ================================================= */}
        <main className="sdna-main-panel">
          {!selectedSubject ? (
            <div className="sdna-select-state">
              <div className="sdna-select-icon">
                <FaBook />
              </div>
              <h2>
                Select a Subject
              </h2>
              <p>
                Choose a subject from the left
                to view and manage its study
                materials.
              </p>
            </div>
          ) : (
            <>
              {/* =================================================*
*&#xA0;                 SUBJECT HEADER*
*&#xA0;             ================================================= */}
              <div className="sdna-selected-header">
                <div className="sdna-selected-icon">
                  <FaBook />
                </div>
                <div className="sdna-selected-info">
                  <span>
                    SELECTED SUBJECT
                  </span>
                  <h1>
                    {selectedSubject.name}
                  </h1>
                  {selectedSubject.description && (
                    <p>
                      {selectedSubject.description}
                    </p>
                  )}
                </div>
                <button
                  type="button"
                  className="sdna-delete-button"
                  onClick={() =>
                    handleDeleteSubject(
                      selectedSubject.id
                    )
                  }
                  title="Delete subject"
                >
                  <FaTrash />
                </button>
              </div>
              {/* =================================================*
*&#xA0;                 STUDY MATERIALS*
*&#xA0;             ================================================= */}
              <section
                className={`sdna-material-panel ${isDragging ? "dragging" : ""}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                <div className="sdna-material-header">
                  <div className="sdna-material-title">
                    <div className="sdna-material-icon">
                      <FaFileAlt />
                    </div>
                    <div>
                      <h2>
                        Study Materials
                      </h2>
                      <p>
                        All uploaded materials
                        for this subject
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    className="sdna-upload-button"
                    onClick={() =>
                      fileInputRef.current?.click()
                    }
                    disabled={uploading}
                  >
                    <FaPlus />
                    Upload Materials
                  </button>
                </div>
                {/* HIDDEN FILE INPUT */}
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept="
                    .pdf,
                    .pptx,
                    .docx,
                    .png,
                    .jpg,
                    .jpeg,
                    .webp
                  "
                  className="sdna-hidden-input"
                  onChange={
                    handleFileChange
                  }
                />
                {/* DOCUMENTS */}
                {renderDocuments()}
                {/* =================================================*
*&#xA0;                   SELECTED FILES*
*&#xA0;               ================================================= */}
                {selectedFiles.length > 0 && (
                  <div className="sdna-selected-upload">
                    <div className="sdna-selected-upload-header">
                      <div>
                        <strong>
                          Selected Files
                        </strong>
                        <span>
                          {selectedFiles.length}{" "}
                          {selectedFiles.length === 1
                            ? "file"
                            : "files"}
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedFiles([]);
                          if (
                            fileInputRef.current
                          ) {
                            fileInputRef.current.value =
                              "";
                          }
                        }}
                        title="Clear selected files"
                      >
                        <FaTimes />
                      </button>
                    </div>
                    <div className="sdna-selected-file-list">
                      {selectedFiles.map(
                        (file, index) => (
                          <div
                            className="sdna-selected-file"
                            key={`${file.name}-${index}`}
                          >
                            <div className="sdna-selected-file-icon">
                              {getFileIcon(
                                file.name
                                  .split(".")
                                  .pop()
                              )}
                            </div>
                            <div className="sdna-selected-file-info">
                              <span
                                className="sdna-selected-file-name"
                                title={file.name}
                              >
                                {file.name}
                              </span>
                              <span className="sdna-selected-file-size">
                                {(file.size / (1024 * 1024)).toFixed(2)} MB
                              </span>
                            </div>
                            <button
                              type="button"
                              className="sdna-selected-file-remove"
                              onClick={() =>
                                setSelectedFiles((current) =>
                                  current.filter((_, i) => i !== index)
                                )
                              }
                              title="Remove file"
                            >
                              <FaTimes />
                            </button>
                          </div>
                        )
                      )}
                    </div>
                    <button
                      type="button"
                      className="sdna-primary-button sdna-upload-submit"
                      onClick={
                        handleUpload
                      }
                      disabled={uploading}
                    >
                      <FaUpload />
                      {uploading
                        ? "Uploading..."
                        : `Upload ${selectedFiles.length} ${
                            selectedFiles.length === 1
                              ? "Material"
                              : "Materials"
                          }`}
                    </button>
                  </div>
                )}
                {/* =================================================*
*&#xA0;                   DROP / UPLOAD AREA*
*&#xA0;               ================================================= */}
              </section>
            </>
          )}
        </main>
      </div>
      {/* =================================================*
        MESSAGE*
     ================================================= */}
      {message && (
        <div
          className={
            messageType === "error"
              ? "sdna-toast error"
              : "sdna-toast success"
          }
        >
          {messageType === "error" ? (
            <FaTimes />
          ) : (
            <FaCheckCircle />
          )}
          <span>
            {message}
          </span>
        </div>
      )}
    </section>
  );
}
export default SubjectManager;
