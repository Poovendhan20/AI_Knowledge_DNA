import {
  useEffect,
  useState,
} from "react";

import {
  FaPlus,
  FaBook,
  FaTrash,
  FaUpload,
  FaFilePdf,
  FaFilePowerpoint,
  FaFileWord,
  FaImage,
} from "react-icons/fa";

import {
  createSubject,
  getSubjects,
  deleteSubject,
  uploadMultipleDocuments,
} from "../services/subjectApi";


function SubjectManager() {

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

  const [
    selectedFiles,
    setSelectedFiles,
  ] = useState([]);

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    uploading,
    setUploading,
  ] = useState(false);

  const [
    message,
    setMessage,
  ] = useState("");


  const loadSubjects = async () => {

    try {

      setLoading(true);

      const result =
        await getSubjects();

      if (result.success) {

        setSubjects(
          result.subjects
        );

      }

    } catch (error) {

      console.error(error);

      setMessage(
        "Unable to load subjects."
      );

    } finally {

      setLoading(false);

    }

  };


  useEffect(() => {

    loadSubjects();

  }, []);


  const handleCreateSubject =
    async (event) => {

      event.preventDefault();

      if (!subjectName.trim()) {

        setMessage(
          "Enter a subject name."
        );

        return;

      }

      try {

        setLoading(true);

        const result =
          await createSubject(
            subjectName,
            description
          );

        if (result.success) {

          setSubjectName("");

          setDescription("");

          setMessage(
            "Subject created successfully."
          );

          await loadSubjects();

        }

      } catch (error) {

        console.error(error);

        setMessage(
          error.response?.data?.message ||
          "Unable to create subject."
        );

      } finally {

        setLoading(false);

      }

    };


  const handleDeleteSubject =
    async (subjectId) => {

      const confirmed =
        window.confirm(
          "Delete this subject?"
        );

      if (!confirmed) {
        return;
      }

      try {

        await deleteSubject(
          subjectId
        );

        if (
          selectedSubject?.id ===
          subjectId
        ) {

          setSelectedSubject(null);

        }

        await loadSubjects();

      } catch (error) {

        console.error(error);

        setMessage(
          "Unable to delete subject."
        );

      }

    };


  const handleFileChange =
    (event) => {

      const files =
        Array.from(
          event.target.files || []
        );

      setSelectedFiles(
        files
      );

    };


  const handleUpload =
    async () => {

      if (!selectedSubject) {

        setMessage(
          "Select a subject first."
        );

        return;

      }

      if (
        selectedFiles.length === 0
      ) {

        setMessage(
          "Select at least one file."
        );

        return;

      }

      try {

        setUploading(true);

        setMessage("");

        const result =
          await uploadMultipleDocuments(
            selectedSubject.id,
            selectedFiles
          );

        if (result.success) {

          setMessage(
            result.message
          );

          setSelectedFiles([]);

        }

      } catch (error) {

        console.error(error);

        setMessage(
          error.response?.data?.message ||
          "Upload failed."
        );

      } finally {

        setUploading(false);

      }

    };


  const getFileIcon =
    (type) => {

      if (type === "pdf") {
        return <FaFilePdf />;
      }

      if (
        type === "pptx"
      ) {
        return <FaFilePowerpoint />;
      }

      if (
        type === "docx"
      ) {
        return <FaFileWord />;
      }

      return <FaImage />;

    };


  return (

    <section className="subject-manager">

      <div className="subject-manager-header">

        <div>

          <span className="dashboard-label">
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


      <div className="subject-layout">

        {/* =================================================
            CREATE SUBJECT
        ================================================= */}

        <div className="subject-create-card">

          <div className="subject-card-icon">
            <FaPlus />
          </div>

          <h3>
            Create Subject
          </h3>

          <p>
            Add a subject for your
            study materials.
          </p>


          <form
            onSubmit={
              handleCreateSubject
            }
          >

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
            />

            <button
              type="submit"
              className="primary-button"
              disabled={loading}
            >
              <FaPlus />
              Create Subject
            </button>

          </form>

        </div>


        {/* =================================================
            SUBJECT LIST
        ================================================= */}

        <div className="subject-list-card">

          <div className="subject-card-header">

            <div>

              <h3>
                Your Subjects
              </h3>

              <span>
                {subjects.length} subject
                {subjects.length !== 1
                  ? "s"
                  : ""}
              </span>

            </div>

          </div>


          {subjects.length === 0 ? (

            <div className="empty-subjects">

              <FaBook />

              <p>
                No subjects yet.
              </p>

              <span>
                Create your first subject
                to organize your materials.
              </span>

            </div>

          ) : (

            <div className="subjects-grid">

              {subjects.map(
                (subject) => (

                  <button
                    key={
                      subject.id
                    }
                    className={
                      selectedSubject?.id ===
                      subject.id
                        ? "subject-item active"
                        : "subject-item"
                    }
                    onClick={() =>
                      setSelectedSubject(
                        subject
                      )
                    }
                  >

                    <div className="subject-item-icon">
                      <FaBook />
                    </div>

                    <div className="subject-item-content">

                      <strong>
                        {subject.name}
                      </strong>

                      <span>
                        {subject.document_count}
                        {" "}
                        documents
                        {" • "}
                        {subject.topic_count}
                        {" "}
                        topics
                      </span>

                    </div>


                    <span
                      className="subject-delete"
                      onClick={(
                        event
                      ) => {

                        event.stopPropagation();

                        handleDeleteSubject(
                          subject.id
                        );

                      }}
                    >

                      <FaTrash />

                    </span>

                  </button>

                )
              )}

            </div>

          )}

        </div>

      </div>


      {/* =================================================
          MULTIPLE UPLOAD
      ================================================= */}

      {selectedSubject && (

        <div className="subject-upload-card">

          <div className="subject-upload-header">

            <div>

              <span>
                SELECTED SUBJECT
              </span>

              <h3>
                {selectedSubject.name}
              </h3>

            </div>

          </div>


          <label
            className="multiple-upload-area"
          >

            <FaUpload />

            <strong>
              Select study materials
            </strong>

            <span>
              You can select multiple
              PDFs, PPTX, DOCX or images.
            </span>

            <input
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
              onChange={
                handleFileChange
              }
            />

          </label>


          {selectedFiles.length > 0 && (

            <div className="selected-files">

              {selectedFiles.map(
                (file, index) => (

                  <div
                    className="selected-file"
                    key={`${file.name}-${index}`}
                  >

                    <span className="file-icon">
                      {getFileIcon(
                        file.name
                          .split(".")
                          .pop()
                          .toLowerCase()
                      )}
                    </span>

                    <span>
                      {file.name}
                    </span>

                  </div>

                )
              )}

            </div>

          )}


          <button
            className="primary-button upload-all-button"
            onClick={
              handleUpload
            }
            disabled={
              uploading ||
              selectedFiles.length === 0
            }
          >

            <FaUpload />

            {uploading
              ? "Uploading..."
              : `Upload ${selectedFiles.length || ""} Material${selectedFiles.length === 1 ? "" : "s"}`}

          </button>

        </div>

      )}


      {message && (

        <div className="subject-message">
          {message}
        </div>

      )}

    </section>

  );

}


export default SubjectManager;