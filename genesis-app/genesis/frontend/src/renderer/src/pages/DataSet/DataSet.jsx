import React, { useEffect, useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faPlus,
  faFileCsv,
  faTrash,
  faEdit,
  faSearch,
  faTimes,
  faUpload,
  faSave,
  faExclamationTriangle
} from "@fortawesome/free-solid-svg-icons";
import Papa from "papaparse";

/* ------------------------
   DatasetManager Component
------------------------ */
const DatasetManager = () => {
  /* ------------------------
     State Management
  ------------------------ */
  // Popup modal message state
  const [popupMessage, setPopupMessage] = useState("");
  const [datasetToShow, setDatasetToShow] = useState([]);
  const [backupDatasets, setBackupDatasets] = useState([]);
  const [backupDatasetToShow, setBackupDatasetToShow] = useState(null);
  const [csv, setCsv] = useState(null);
  const [csvPreview, setCsvPreview] = useState([]);
  const [headers, setHeaders] = useState([]);
  const [errors, setErrors] = useState([]);
  const [rowAddError, setRowAddError] = useState([]);

  const [showingBackup, setShowingBackup] = useState(false);
  const [selectedBackupName, setSelectedBackupName] = useState("");


  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState("row");

  const [searchRow, setSearchRow] = useState("");
  const [editingRowIndex, setEditingRowIndex] = useState(null);
  const [editingRowData, setEditingRowData] = useState({});

  const [newRowData, setNewRowData] = useState(initialNewRow());

  const [filteredRows, setFilteredRows] = useState([]);
  // New state for row editing modal in CSV manager
  const [isEditing, setIsEditing] = useState(false);

  // State for delete confirmations
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState({ type: null, index: null });
  const [headerDeleteConfirm, setHeaderDeleteConfirm] = useState("");

  /* ------------------------
     Lifecycle Effects
  ------------------------ */
  useEffect(() => {
    window.electron.ipcRenderer.send("open-dataset-for-first-load");
    window.electron.ipcRenderer.send("list-all-backup-datasets");
  }, []);

  useEffect(() => {
    // listen dataset by name
    window.electron.ipcRenderer.on("opened-backup-dataset-by-name", (_, event) => {
      setBackupDatasetToShow(Papa.parse(event.dataset, { header: true }).data);
      console.log(event.dataset);
    })
    return () => {
      window.electron.ipcRenderer.removeAllListeners("opened-backup-dataset-by-name");
    }
  }, []);

  useEffect(() => {
    const listener = (_, event) => {
      setDatasetToShow(Papa.parse(event.dataset, { header: true }).data);
    };
    window.electron.ipcRenderer.on("opened-dataset-for-first-load", listener);
    return () => {
      window.electron.ipcRenderer.removeListener("opened-dataset-for-first-load", listener);
    };
  }, []);

  useEffect(() => {
    const listener = (_, event) => {
      setBackupDatasets(event.datasets);
      console.log(event.datasets);
    };
    window.electron.ipcRenderer.on("listed-all-backup-datasets", listener);
    return () => {
      window.electron.ipcRenderer.removeListener("listed-all-backup-datasets", listener);
    };
  }, [])

  useEffect(() => {
    // CSV validation listeners
    window.electron.ipcRenderer.on("csv-validation-success", () => {
      setPopupMessage("CSV uploaded successfully!");
      resetCsvStates();
    });

    window.electron.ipcRenderer.on("csv-validation-failed", (_, errs) => {
      setErrors(errs);
    });

    window.electron.ipcRenderer.on("csv-parsing-failed", () => {
      setErrors([{ reason: "Critical parsing error" }]);
    });


    // Row validation listeners
    window.electron.ipcRenderer.on("add-row-success", () => {
      setPopupMessage("Row added successfully!");
    });

    window.electron.ipcRenderer.on("add-row-failed", (_, errs) => {
      setRowAddError(errs);
    });

    // Cleanup listeners on unmount
    return () => {
      window.electron.ipcRenderer.removeAllListeners("csv-validation-success");
      window.electron.ipcRenderer.removeAllListeners("csv-validation-failed");
      window.electron.ipcRenderer.removeAllListeners("csv-parsing-failed");
      window.electron.ipcRenderer.removeAllListeners("add-row-success");
      window.electron.ipcRenderer.removeAllListeners("add-row-failed");
    };
  }, []);

  useEffect(() => {
    if (searchRow) {
      const query = searchRow.toLowerCase();
      const results = csvPreview.filter(row =>
        Object.values(row).some(value =>
          String(value).toLowerCase().includes(query)
        )
      );
      setFilteredRows(results);
    } else {
      setFilteredRows(csvPreview);
    }
  }, [searchRow, csvPreview]);

  /* ------------------------
     Row CRUD Handlers
  ------------------------ */
  const handleAddRowSubmit = (e) => {
    e.preventDefault();
    setErrors([]);
    window.electron.ipcRenderer.send("add-row", newRowData);
  };

  const handleUpdateRow = (e) => {
    e.preventDefault();
    if (editingRowIndex === null) return;

    const updatedData = [...csvPreview];
    updatedData[editingRowIndex] = editingRowData;

    setCsvPreview(updatedData);
    setCsv(Papa.unparse(updatedData, { header: true, skipEmptyLines: "greedy" }));

    setEditingRowIndex(null);
    setEditingRowData({});
    setIsEditing(false);
    setPopupMessage("Row updated successfully!");
  };

  const handleDeleteRow = (index) => {
    const updatedData = csvPreview.filter((_, i) => i !== index);
    setCsvPreview(updatedData);
    setCsv(Papa.unparse(updatedData, { header: true, skipEmptyLines: "greedy" }));
    setShowDeleteConfirm(false);
  };

  /* ------------------------
     Header Handlers
  ------------------------ */
  const handleHeaderChange = (index, newValue) => {
    const oldHeader = headers[index];
    const updatedHeaders = [...headers];
    updatedHeaders[index] = newValue;

    const updatedRows = csvPreview.map((row) => {
      const newRow = { ...row };

      if (oldHeader === "__parsed_extra" && Array.isArray(newRow[oldHeader])) {
        newRow[newValue] = newRow[oldHeader].join(", ");
        delete newRow[oldHeader];
      } else if (oldHeader in newRow) {
        newRow[newValue] = newRow[oldHeader];
        delete newRow[oldHeader];
      }

      return newRow;
    });

    setHeaders(updatedHeaders);
    setCsvPreview(updatedRows);

    const newCsv = Papa.unparse(updatedRows, {
      header: true,
      columns: updatedHeaders,
      skipEmptyLines: "greedy",
    });
    setCsv(newCsv);
  };

  const handleAddHeader = () => {
    const newHeader = `NewColumn_${headers.length + 1}`;
    const updatedHeaders = [...headers, newHeader];
    const updatedRows = csvPreview.map((row) => ({ ...row, [newHeader]: "" }));

    setHeaders(updatedHeaders);
    setCsvPreview(updatedRows);
    setCsv(Papa.unparse(updatedRows, { header: true, columns: updatedHeaders }));
  };

  const handleDeleteHeader = (index) => {
    if (headerDeleteConfirm !== headers[index]) {
      setPopupMessage(`Please type "${headers[index]}" to confirm deletion`);
      return;
    }

    const updatedHeaders = headers.filter((_, i) => i !== index);
    const updatedRows = csvPreview.map((row) => {
      const newRow = { ...row };
      delete newRow[headers[index]];
      return newRow;
    });

    setHeaders(updatedHeaders);
    setCsvPreview(updatedRows);
    setCsv(Papa.unparse(updatedRows, { header: true, columns: updatedHeaders }));
    setHeaderDeleteConfirm("");
    setShowDeleteConfirm(false);
  };

  /* ------------------------
     CSV File Handlers
  ------------------------ */
  const handleSaveCSV = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const text = await file.text();
    setCsv(text);

    const parsed = Papa.parse(text, { header: true, skipEmptyLines: "greedy" });
    setCsvPreview(parsed.data);

    const fields = parsed.meta.fields || [];
    const hasExtra = parsed.data.some((row) => row.__parsed_extra);
    if (hasExtra && !fields.includes("__parsed_extra")) fields.push("__parsed_extra");

    setHeaders(fields);
  };

  const handleUploadCSV = () => {
    if (!csv) return;
    setErrors([]);
    window.electron.ipcRenderer.send("update-and-validate-csv", csv);
  };

  /* ------------------------
     Modal Management
  ------------------------ */
  const handleOpenModal = (type) => {
    setModalType(type);
    setShowModal(true);
    setErrors([]);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    resetCsvStates();
  };

  /* ------------------------
     Delete Confirmation
  ------------------------ */
  const confirmDelete = (type, index) => {
    setDeleteTarget({ type, index });
    setShowDeleteConfirm(true);
  };

  /* ------------------------
     Helpers
  ------------------------ */
  function resetCsvStates() {
    setCsv(null);
    setCsvPreview([]);
    setErrors([]);
    setSearchRow("");
    setEditingRowIndex(null);
    setEditingRowData({});
    setHeaders([]);
  }

  function initialNewRow() {
    return {
      chr: "", start: "", end: "", ref: "", alt: "", class: "", gene: "", phastconselements100way: "", phylop100way_vertebrate: "", phylop20way_mammalian: "", phastcons100way_vertebrate: "", phastcons20way_mammalian: "", siphy_29way_logodds: "", phylop30way_mammalian: "", phastcons30way_mammalian: "", af: "", af_raw: "", af_male: "", af_female: "", af_afr: "", af_ami: "", af_amr: "", af_asj: "", af_eas: "", af_fin: "", af_nfe: "", af_oth: "", gdi: "", gdi_phred: "", rvis1: "", rvis2: "", lof_score: "", molecular_weight: "", equipotential_point: "", hydrophilic: "", hydrophobic: "", amphipathic_: "", cyclic: "", essential: "", aromatic: "", aliphatic: "", nonpolar: "", polar_uncharged: "", acidic: "", basic: "", sulfur: "", pka_cooh: "", pka_nh3: "", blosum100: "", ds_ag: "", ds_al: "", ds_dg: "", ds_dl: "", dp_ag: "", dp_al: "", dp_dg: "", dp_dl: "", gm12878: "", h1hesc: "", hepg2: "", hmec: "", hsmm: "", huvec: "", k562: "", nhek: "", nhlf: "", func_frameshift: "", func_nonframeshift: "", func_nonsynonymous_snv: "", func_startloss: "", func_stopgain: "", func_stoploss: "", omim_autosomal_dominant: "", omim_autosomal_recessive: "", omim_x_linked_dominant: "", omim_x_linked_recessive: "", omim_other: ""
    };
  }

  // State for DatasetTable pagination
  const [mainTablePage, setMainTablePage] = useState(1);
  const [mainRowsPerPage, setMainRowsPerPage] = useState(10);
  const [mainPaginatedRows, setMainPaginatedRows] = useState([]);
  const [mainTotalRows, setMainTotalRows] = useState(0);

  // Handler for DatasetTable to update pagination info
  const handleMainTableChange = (info) => {
    setMainPaginatedRows(info.paginatedRows);
    setMainTotalRows(info.totalRows);
    setMainTablePage(info.currentPage);
    setMainRowsPerPage(info.rowsPerPage);
  };

  // Derived: calculate current row display range
  const mainStartIdx = (mainTablePage - 1) * mainRowsPerPage + 1;
  const mainEndIdx = Math.min(mainStartIdx + mainPaginatedRows.length - 1, mainTotalRows);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6 flex-1">
      {/* Header Section centered on top */}
      <HeaderSection onOpenModal={handleOpenModal} />

      <div className="grid grid-cols-1 gap-6 mt-6">
        {/* Main Content */}
        <div className="col-span-1">
          <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">

            <div className="flex justify-between items-center mb-6">
              <div className="flex items-center space-x-3">
                <h2 className="text-2xl font-bold text-gray-800">
                  {showingBackup
                    ? `Backup Dataset: ${selectedBackupName || "Unnamed"}`
                    : "Current Dataset"}
                </h2>


                {/* Dataset Selector */}
                <select
                  value={selectedBackupName}
                  onChange={(e) => {
                    const name = e.target.value;
                    setSelectedBackupName(name);
                    if (name) {
                      window.electron.ipcRenderer.send("open-backup-dataset-by-name", name);
                      setShowingBackup(true);
                    }
                  }}
                  className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:ring-[#0098B0] focus:border-[#0098B0]"
                >
                  <option value="">-- Select Backup Dataset --</option>
                  {backupDatasets.map((name) => (
                    <option key={name} value={name}>
                      {name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Show Current Dataset Button */}
              <button
                onClick={() => {
                  setShowingBackup(false);
                  setSelectedBackupName("");
                }}
                className="bg-[#0098B0] hover:bg-[#007a96] text-white text-sm px-4 py-2 rounded-md shadow-sm transition-all"
              >
                Show Current Dataset
              </button>
            </div>
            <div className="text-sm text-gray-500 mb-4">
              {mainTotalRows > 0
                ? `Showing ${mainStartIdx}${mainEndIdx !== mainStartIdx ? `-${mainEndIdx}` : ""} of ${mainTotalRows} rows`
                : "No rows"}
            </div>

            {(showingBackup ? (backupDatasetToShow?.length || 0) : datasetToShow.length) === 1 ? (
              <div className="flex flex-col items-center justify-center text-center text-gray-500 py-16 border border-dashed border-gray-300 rounded-xl bg-gray-50">
                <FontAwesomeIcon icon={faExclamationTriangle} className="text-[#0098B0] text-4xl mb-4" />
                <p className="text-lg font-medium">No data added since the last training session.</p>
                <p className="text-sm text-gray-400 mt-1">
                  Upload a new dataset or add rows to begin again.
                </p>
              </div>
            ) : (
              <DatasetTable
                dataset={showingBackup ? backupDatasetToShow || [] : datasetToShow}
                currentPage={mainTablePage}
                rowsPerPage={mainRowsPerPage}
                onChange={handleMainTableChange}
              />
            )}



            {/* Pagination Controls */}
            <div className="flex flex-wrap items-center justify-between mt-4 px-2 py-2">
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600">Rows per page:</span>
                <select
                  value={mainRowsPerPage}
                  onChange={e => {
                    setMainRowsPerPage(Number(e.target.value));
                    setMainTablePage(1);
                  }}
                  className="border border-gray-300 rounded px-2 py-1 text-sm"
                >
                  {[5, 10, 20, 50, 100].map(opt => (
                    <option key={opt} value={opt}>{opt}</option>
                  ))}
                </select>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setMainTablePage(prev => Math.max(prev - 1, 1))}
                  disabled={mainTablePage === 1}
                  className="px-3 py-1.5 rounded bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm disabled:opacity-50"
                >
                  Previous
                </button>
                <span className="text-sm text-gray-600">
                  Page {mainTablePage} of {Math.max(1, Math.ceil(mainTotalRows / mainRowsPerPage) || 1)}
                </span>
                <button
                  onClick={() => setMainTablePage(prev => Math.min(prev + 1, Math.max(1, Math.ceil(mainTotalRows / mainRowsPerPage) || 1)))}
                  disabled={mainTablePage === Math.max(1, Math.ceil(mainTotalRows / mainRowsPerPage) || 1)}
                  className="px-3 py-1.5 rounded bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {showModal && (
        <DatasetModal
          type={modalType}
          onClose={handleCloseModal}
          setErrors={setErrors}
          {...{
            csvPreview,
            headers,
            errors,
            searchRow,
            editingRowIndex,
            editingRowData,
            newRowData,
            setSearchRow,
            setEditingRowData,
            setEditingRowIndex,
            setNewRowData,
            handleAddRowSubmit,
            handleUpdateRow,
            handleDeleteRow: confirmDelete,
            handleHeaderChange,
            handleAddHeader,
            handleDeleteHeader: confirmDelete,
            handleSaveCSV,
            handleUploadCSV,
            filteredRows,
            isEditing,
            setIsEditing,
          }}
        />
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <DeleteConfirmationModal
          deleteTarget={deleteTarget}
          headers={headers}
          headerDeleteConfirm={headerDeleteConfirm}
          setHeaderDeleteConfirm={setHeaderDeleteConfirm}
          onConfirm={() => {
            if (deleteTarget.type === "row") {
              handleDeleteRow(deleteTarget.index);
            } else if (deleteTarget.type === "header") {
              handleDeleteHeader(deleteTarget.index);
            }
          }}
          onCancel={() => {
            setShowDeleteConfirm(false);
            setHeaderDeleteConfirm("");
          }}
        />
      )}
      {/* Popup Modal */}
      {popupMessage && (
        <PopupModal message={popupMessage} onClose={() => setPopupMessage("")} />
      )}
    </div>
  );
};

/* ------------------------
   Sub-Components
------------------------ */
const HeaderSection = ({ onOpenModal }) => (
  <div className="text-center mb-10 mt-5">
    <h1 className="text-5xl font-bold text-[#0098B0] mb-2">Dataset Management</h1>
    <div className="w-24 h-1.5 bg-gradient-to-r from-[#0098B0]/40 to-[#0098B0]/10 mx-auto mb-4 rounded-full"></div>
    <p className="text-gray-600 text-lg max-w-2xl mx-auto">
      View, edit, and validate your training datasets with our intuitive management tools
    </p>

    <div className="flex justify-center space-x-4 mt-8">
      <ActionButton
        icon={faPlus}
        text="Add Row"
        onClick={() => onOpenModal("row")}
        className="bg-[#0098B0] hover:bg-[#007a96] text-amber-50"
      />
      <ActionButton
        icon={faFileCsv}
        text="Upload CSV"
        onClick={() => onOpenModal("csv")}
        className="bg-white text-[#0098B0] border border-[#0098B0] hover:bg-gray-50"
      />
    </div>
  </div>
);

const ActionButton = ({ icon, text, onClick, className = "" }) => (
  <button
    onClick={onClick}
    className={`px-6 py-3 rounded-xl shadow-sm transition-all duration-200 hover:shadow-md flex items-center space-x-2 font-medium ${className}`}
  >
    <FontAwesomeIcon icon={icon} />
    <span>{text}</span>
  </button>
);

// DatasetTable now only handles table display and returns pagination data to parent
const DatasetTable = ({
  dataset,
  currentPage = 1,
  rowsPerPage = 10,
  onChange,
}) => {
  // Calculate paginated rows
  const totalRows = dataset.length;
  const totalPages = Math.ceil(totalRows / rowsPerPage) || 1;
  const startIdx = (currentPage - 1) * rowsPerPage;
  const endIdx = startIdx + rowsPerPage;
  const paginatedRows = dataset.slice(startIdx, endIdx);

  // Communicate pagination state to parent
  React.useEffect(() => {
    if (onChange) {
      onChange({
        paginatedRows,
        totalRows,
        currentPage,
        rowsPerPage,
      });
    }
    // eslint-disable-next-line
  }, [dataset, currentPage, rowsPerPage, totalRows]);

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-x-auto overflow-y-auto max-h-[70vh]">
      <table className="w-full text-left border-collapse">
        <thead className="bg-gradient-to-r from-[#0098B0] to-[#00acc1] sticky top-0 z-10">
          <tr>
            {dataset.length > 0 &&
              Object.keys(dataset[0]).map((key) => (
                <th key={key} className="px-6 py-4 font-semibold text-white text-sm uppercase tracking-wider">
                  {key}
                </th>
              ))}
            <th className="px-6 py-4 font-semibold text-white text-sm uppercase tracking-wider">Actions</th>
          </tr>
        </thead>
        <tbody>
          {paginatedRows.map((row, idx) => (
            <tr key={startIdx + idx} className="border-b border-gray-100 last:border-0 hover:bg-gray-50 transition-colors">
              {Object.keys(row).map((key) => (
                <td key={key} className="px-6 py-4 text-gray-700">{row[key]}</td>
              ))}
              <td className="px-6 py-4">
                <div className="flex space-x-2">
                  <button className="text-[#0098B0] hover:text-[#007a96] transition-colors p-2 rounded-lg hover:bg-blue-50">
                    <FontAwesomeIcon icon={faEdit} />
                  </button>
                  <button className="text-red-500 hover:text-red-700 transition-colors p-2 rounded-lg hover:bg-red-50">
                    <FontAwesomeIcon icon={faTrash} />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

/* ------------------------
   DatasetModal Component
   (Row Form / CSV Upload)
------------------------ */
const DatasetModal = (props) => {
  const { type, onClose, setErrors } = props;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
      <div className="bg-white p-8 rounded-2xl shadow-2xl w-full max-w-5xl max-h-[95vh] flex flex-col overflow-hidden">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800">
            {type === "row" ? "Add New Row" : "CSV Manager"}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 p-2 rounded-full hover:bg-gray-100 transition-colors"
          >
            <FontAwesomeIcon icon={faTimes} />
          </button>
        </div>

        <div className="overflow-y-auto flex-1 pr-2">
          {type === "row" ? <RowForm {...props} /> : <CsvManager {...props} setErrors={setErrors} />}
        </div>
      </div>
    </div>
  );
};

/* ------------------------
   Helper Components
------------------------ */
const RowForm = ({ newRowData, setNewRowData, handleAddRowSubmit, errors }) => (
  <form onSubmit={handleAddRowSubmit} className="space-y-6">
    <div className="grid grid-cols-2 gap-4">
      {Object.keys(newRowData).map((field) => (
        <div key={field} className="flex flex-col">
          <label className="text-sm font-medium text-gray-700 mb-1 capitalize">
            {field.replace(/_/g, " ")}
          </label>
          <input
            type="text"
            value={newRowData[field]}
            onChange={(e) => setNewRowData({ ...newRowData, [field]: e.target.value })}
            className="border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-[#0098B0]/30 focus:border-[#0098B0] outline-none transition-all"
          />
        </div>
      ))}
    </div>

    {errors.length > 0 && (
      <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl text-sm">
        <h3 className="font-semibold mb-2 flex items-center">
          <FontAwesomeIcon icon={faTimes} className="mr-2" />
          Validation Errors:
        </h3>
        <ul className="list-disc pl-5 space-y-1">
          {errors.map((err, idx) => (
            <li key={idx}>{err.reason}</li>
          ))}
        </ul>
      </div>
    )}

    <div className="flex justify-end space-x-3 pt-4">
      <button
        type="button"
        onClick={() => setNewRowData(initialNewRow())}
        className="px-5 py-2.5 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
      >
        Reset
      </button>
      <button
        type="submit"
        className="bg-[#0098B0] text-white px-5 py-2.5 rounded-lg hover:bg-[#007a96] transition-colors flex items-center space-x-2"
      >
        <FontAwesomeIcon icon={faPlus} />
        <span>Add Row</span>
      </button>
    </div>
  </form>
);

const CsvManager = ({
  csvPreview,
  headers,
  errors,
  searchRow,
  setSearchRow,
  editingRowIndex,
  editingRowData,
  setEditingRowData,
  setEditingRowIndex,
  handleUpdateRow,
  handleDeleteRow,
  handleHeaderChange,
  handleAddHeader,
  handleDeleteHeader,
  handleSaveCSV,
  handleUploadCSV,
  filteredRows,
  isEditing,
  setIsEditing,
  setErrors,
}) => {
  // State for sort
  const [sortColumn, setSortColumn] = React.useState("");
  const [sortOrder, setSortOrder] = React.useState("asc");

  // Pagination state for table (not for search results)
  const [currentPage, setCurrentPage] = React.useState(1);
  const [rowsPerPage, setRowsPerPage] = React.useState(10);

  // New state for row number search
  const [searchRowNumber, setSearchRowNumber] = React.useState("");

  // Derived: filtered and sorted rows
  const [displayRows, setDisplayRows] = React.useState(filteredRows);

  // Header editing modal state
  const [editingHeaderIndex, setEditingHeaderIndex] = React.useState(null);
  const [editingHeaderValue, setEditingHeaderValue] = React.useState("");

  // Update displayRows whenever dependencies change
  React.useEffect(() => {
    let rows = csvPreview;
    // If searching by row number, take precedence
    if (searchRowNumber && !isNaN(Number(searchRowNumber))) {
      const idx = Number(searchRowNumber) - 1;
      if (idx >= 0 && idx < csvPreview.length) {
        rows = [csvPreview[idx]];
      } else {
        rows = [];
      }
    } else if (searchRow) {
      // Keyword search
      const query = searchRow.toLowerCase();
      rows = csvPreview.filter(row =>
        Object.values(row).some(value =>
          String(value).toLowerCase().includes(query)
        )
      );
    } else {
      // No search
      rows = csvPreview;
    }
    // Sorting
    if (sortColumn) {
      rows = [...rows].sort((a, b) => {
        const aVal = a[sortColumn] ?? "";
        const bVal = b[sortColumn] ?? "";
        // Numeric sort if both are numbers, else string
        const aNum = parseFloat(aVal);
        const bNum = parseFloat(bVal);
        let cmp = 0;
        if (!isNaN(aNum) && !isNaN(bNum)) {
          cmp = aNum - bNum;
        } else {
          cmp = String(aVal).localeCompare(String(bVal));
        }
        return sortOrder === "asc" ? cmp : -cmp;
      });
    }
    setDisplayRows(rows);
  }, [csvPreview, sortColumn, sortOrder, searchRow, searchRowNumber]);

  // Keep filteredRows in sync for legacy code (if filteredRows changes, but not used for search anymore)
  React.useEffect(() => {
    setDisplayRows(filteredRows);
  }, [filteredRows]);

  // Pagination for CSV main preview table
  const totalRows = displayRows.length;
  const totalPages = Math.ceil(totalRows / rowsPerPage) || 1;
  const startIdx = (currentPage - 1) * rowsPerPage;
  const endIdx = startIdx + rowsPerPage;
  const paginatedRows = displayRows.slice(startIdx, endIdx);

  React.useEffect(() => {
    // Reset to first page if displayRows changes and current page is out of range
    if (currentPage > totalPages) {
      setCurrentPage(1);
    }
  }, [displayRows, rowsPerPage]);

  const cancelEdit = () => {
    setEditingRowIndex(null);
    setEditingRowData({});
    setIsEditing(false);
  };

  // Header Modal handlers
  const openHeaderEditModal = (idx) => {
    setEditingHeaderIndex(idx);
    setEditingHeaderValue(headers[idx]);
  };
  const closeHeaderEditModal = () => {
    setEditingHeaderIndex(null);
    setEditingHeaderValue("");
  };
  const confirmHeaderEdit = () => {
    if (
      editingHeaderValue.trim() &&
      editingHeaderValue !== headers[editingHeaderIndex]
    ) {
      handleHeaderChange(editingHeaderIndex, editingHeaderValue.trim());
    }
    closeHeaderEditModal();
  };

  return (
    <div className="flex flex-col space-y-6 flex-1 overflow-auto">
      {/* File Upload Section */}
      <div className="flex flex-col items-center space-y-4 p-6 border-2 border-dashed border-gray-300 rounded-2xl bg-gray-50">
        <div className="p-4 bg-white rounded-full shadow-sm">
          <FontAwesomeIcon icon={faFileCsv} className="text-4xl text-[#0098B0]" />
        </div>
        <div className="text-center">
          <h3 className="font-medium text-gray-700 mb-1">Upload CSV File</h3>
          <p className="text-sm text-gray-500">Supported format: .csv</p>
        </div>
        <label className="cursor-pointer bg-[#0098B0] text-white px-5 py-2.5 rounded-lg hover:bg-[#007a96] transition-colors flex items-center space-x-2">
          <FontAwesomeIcon icon={faUpload} />
          <span>Choose File</span>
          <input
            onChange={handleSaveCSV}
            type="file"
            accept=".csv"
            className="hidden"
          />
        </label>
      </div>

      {/* Header Editor */}
      {headers.length > 0 && (
        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-medium text-gray-700">Edit Headers</h3>
            <button
              onClick={handleAddHeader}
              className="text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1.5 rounded-lg transition-colors flex items-center space-x-1"
            >
              <FontAwesomeIcon icon={faPlus} size="xs" />
              <span>Add Column</span>
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 max-h-60 overflow-y-auto p-1">
            {headers.map((h, i) => (
              <div key={i} className="flex items-center space-x-2 p-2 bg-gray-50 rounded-lg">
                <span className="flex-1 text-sm truncate">{h}</span>
                <button
                  onClick={() => openHeaderEditModal(i)}
                  className="text-[#0098B0] hover:text-[#007a96] p-1.5 rounded hover:bg-blue-50 transition-colors"
                  title="Edit header"
                  type="button"
                >
                  <FontAwesomeIcon icon={faEdit} size="xs" />
                </button>
                <button
                  onClick={() => handleDeleteHeader("header", i)}
                  className="text-red-500 hover:text-red-700 p-1.5 rounded hover:bg-red-50 transition-colors"
                  title="Delete header"
                  type="button"
                >
                  <FontAwesomeIcon icon={faTrash} size="xs" />
                </button>
              </div>
            ))}
          </div>
          {/* Header Edit Modal */}
          {editingHeaderIndex !== null && (
            <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
              <div className="bg-white p-6 rounded-2xl shadow-2xl w-full max-w-xs">
                <div className="flex justify-between items-center mb-4">
                  <h4 className="text-lg font-semibold text-gray-800">Edit Header</h4>
                  <button
                    onClick={closeHeaderEditModal}
                    className="text-gray-500 hover:text-gray-700 p-1 rounded-full hover:bg-gray-100 transition-colors"
                  >
                    <FontAwesomeIcon icon={faTimes} />
                  </button>
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Column Name</label>
                  <input
                    type="text"
                    value={editingHeaderValue}
                    onChange={e => setEditingHeaderValue(e.target.value)}
                    className="border border-gray-300 rounded-lg px-4 py-2.5 w-full focus:ring-2 focus:ring-[#0098B0]/30 focus:border-[#0098B0] outline-none transition-all"
                  />
                </div>
                <div className="flex justify-end space-x-2 pt-2">
                  <button
                    onClick={closeHeaderEditModal}
                    className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={confirmHeaderEdit}
                    className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2"
                    disabled={
                      !editingHeaderValue.trim() ||
                      editingHeaderValue === headers[editingHeaderIndex]
                    }
                  >
                    <FontAwesomeIcon icon={faSave} />
                    <span>Save</span>
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Search Section with Results */}
      {csvPreview.length > 0 && (
        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
          <h3 className="font-medium text-gray-700 mb-2">Search Rows</h3>
          <div className="flex flex-col md:flex-row md:items-center md:space-x-2 space-y-2 md:space-y-0">
            {/* Search input */}
            <div className="relative flex-1">
              <FontAwesomeIcon icon={faSearch} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search rows by keyword"
                value={searchRow}
                onChange={(e) => setSearchRow(e.target.value)}
                className="border border-gray-300 rounded-lg pl-10 pr-4 py-2.5 w-full focus:ring-2 focus:ring-[#0098B0]/30 focus:border-[#0098B0] outline-none transition-all"
                disabled={!!searchRowNumber}
              />
              {searchRow && (
                <button
                  onClick={() => setSearchRow("")}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100 transition-colors p-1"
                  tabIndex={-1}
                  type="button"
                >
                  <FontAwesomeIcon icon={faTimes} />
                </button>
              )}
            </div>
            {/* Row number search input */}
            <div className="relative flex-1">
              <label className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 text-xs pointer-events-none">
                Row Number
              </label>
              <input
                type="number"
                min="1"
                placeholder="Row Number"
                value={searchRowNumber}
                onChange={e => setSearchRowNumber(e.target.value.replace(/[^0-9]/g, ""))}
                className="border border-gray-300 rounded-lg pl-24 pr-4 py-2.5 w-full focus:ring-2 focus:ring-[#0098B0]/30 focus:border-[#0098B0] outline-none transition-all"
                disabled={!!searchRow}
              />
              {searchRowNumber && (
                <button
                  onClick={() => setSearchRowNumber("")}
                  className="absolute right-10 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100 transition-colors p-1"
                  tabIndex={-1}
                  type="button"
                >
                  <FontAwesomeIcon icon={faTimes} />
                </button>
              )}
            </div>
            {/* Sort dropdown */}
            <div className="flex items-center space-x-2">
              <label className="text-sm text-gray-600">Sort by:</label>
              <select
                value={sortColumn}
                onChange={e => setSortColumn(e.target.value)}
                className="border border-gray-300 rounded-lg px-2 py-2 text-sm focus:ring-2 focus:ring-[#0098B0]/30 focus:border-[#0098B0] outline-none"
              >
                <option value="">None</option>
                {headers.map((h, idx) => (
                  <option key={h + idx} value={h}>{h}</option>
                ))}
              </select>
              <select
                value={sortOrder}
                onChange={e => setSortOrder(e.target.value)}
                className="border border-gray-300 rounded-lg px-2 py-2 text-sm focus:ring-2 focus:ring-[#0098B0]/30 focus:border-[#0098B0] outline-none"
                disabled={!sortColumn}
              >
                <option value="asc">Asc</option>
                <option value="desc">Desc</option>
              </select>
            </div>
          </div>

          {/* Search Results */}
          {(!!searchRow || !!searchRowNumber) && displayRows.length > 0 && (
            <div className="mt-4 border border-gray-200 rounded-lg max-h-64 overflow-y-auto overflow-x-auto">
              <div className="bg-gray-50 px-4 py-2 font-medium text-sm text-gray-700">
                Search Results
              </div>
              <table className="min-w-max text-sm">
                <thead className="bg-gray-100">
                  <tr>
                    {Object.keys(displayRows[0]).map((key) => (
                      <th key={key} className="px-4 py-2 text-left font-medium text-gray-700 border-b">
                        {key}
                      </th>
                    ))}
                    <th className="px-4 py-2 border-b">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {displayRows.map((row, idx) => (
                    <tr key={`row-${idx}`} className="border-b">
                      {Object.keys(row).map((key) => (
                        <td key={`${idx}-${key}`} className="px-4 py-2 max-w-xs truncate">
                          {row[key]}
                        </td>
                      ))}
                      <td className="px-4 py-2">
                        <div className="flex space-x-2">
                          <button
                            onClick={() => {
                              // For row number search, idx is always 0, so actual index is searchRowNumber-1
                              let actualIdx = idx;
                              if (searchRowNumber && !isNaN(Number(searchRowNumber))) {
                                actualIdx = Number(searchRowNumber) - 1;
                              }
                              setEditingRowIndex(actualIdx);
                              setEditingRowData({ ...row });
                              setIsEditing(true);
                            }}
                            className="text-[#0098B0] hover:text-[#007a96] p-1 rounded hover:bg-blue-50 transition-colors"
                            title="Edit row"
                          >
                            <FontAwesomeIcon icon={faEdit} />
                          </button>
                          <button
                            onClick={() => {
                              let actualIdx = idx;
                              if (searchRowNumber && !isNaN(Number(searchRowNumber))) {
                                actualIdx = Number(searchRowNumber) - 1;
                              }
                              handleDeleteRow("row", actualIdx);
                            }}
                            className="text-red-500 hover:text-red-700 p-1 rounded hover:bg-red-50 transition-colors"
                            title="Delete row"
                          >
                            <FontAwesomeIcon icon={faTrash} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {(!!searchRow || !!searchRowNumber) && displayRows.length === 0 && (
            <div className="mt-4 text-sm text-gray-500 text-center py-4">
              {searchRowNumber
                ? `No row found for row number "${searchRowNumber}"`
                : `No results found for "${searchRow}"`}
            </div>
          )}
        </div>
      )}

      {/* CSV Validation Errors Modal */}
      {errors.length > 0 && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
          <div className="bg-white p-6 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] flex flex-col">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold text-red-600 flex items-center">
                <FontAwesomeIcon icon={faExclamationTriangle} className="mr-2" />
                CSV Validation Errors
              </h3>
              <button
                onClick={() => {
                  // Clear errors to dismiss modal
                  if (setErrors) setErrors([]);
                }}
                className="text-gray-500 hover:text-gray-700 p-1 rounded-full hover:bg-gray-100 transition-colors"
                aria-label="Close"
              >
                <FontAwesomeIcon icon={faTimes} />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto border border-red-100 bg-red-50 rounded-xl p-4">
              <ul className="list-disc pl-5 space-y-1 text-red-700 text-sm">
                {errors.map((err, idx) => (
                  <li key={idx}>
                    {err.row ? `Row ${err.row}${err.col ? `, Col ${err.col}` : ""}: ${err.reason}` : err.reason}
                  </li>
                ))}
              </ul>
            </div>
            <div className="flex justify-end mt-4">
              <button
                onClick={() => {
                  if (setErrors) setErrors([]);
                }}
                className="bg-[#0098B0] text-white px-5 py-2.5 rounded-lg hover:bg-[#007a96] transition-colors font-medium"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CSV Table - Only show when not searching */}
      {csvPreview.length > 0 && !searchRow && (
        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
          <h3 className="font-medium text-gray-700 mb-3">
            CSV Preview ({csvPreview.length} rows)
          </h3>
          {/* Sort controls above preview table */}
          <div className="flex flex-wrap items-center space-x-2 mb-2">
            <div className="flex items-center space-x-1">
              <label className="text-sm text-gray-600">Sort by:</label>
              <select
                value={sortColumn}
                onChange={e => setSortColumn(e.target.value)}
                className="border border-gray-300 rounded-lg px-2 py-1 text-sm focus:ring-2 focus:ring-[#0098B0]/30 focus:border-[#0098B0] outline-none"
              >
                <option value="">None</option>
                {headers.map((h, idx) => (
                  <option key={h + idx} value={h}>{h}</option>
                ))}
              </select>
              <select
                value={sortOrder}
                onChange={e => setSortOrder(e.target.value)}
                className="border border-gray-300 rounded-lg px-2 py-1 text-sm focus:ring-2 focus:ring-[#0098B0]/30 focus:border-[#0098B0] outline-none"
                disabled={!sortColumn}
              >
                <option value="asc">Asc</option>
                <option value="desc">Desc</option>
              </select>
            </div>
          </div>
          <div className="overflow-auto border border-gray-200 rounded-lg max-h-96">
            <table className="min-w-full text-left border-collapse text-sm">
              <thead className="bg-gray-100 sticky top-0 z-10">
                <tr>
                  {Object.keys(csvPreview[0]).map((key) => (
                    <th key={key} className="px-4 py-2.5 font-semibold text-gray-700 text-xs uppercase tracking-wider border-b border-gray-300">
                      {key}
                    </th>
                  ))}
                  <th className="px-4 py-2.5 border-b border-gray-300">Actions</th>
                </tr>
              </thead>
              <tbody>
                {paginatedRows.map((row, idx) => {
                  const globalIdx = startIdx + idx;
                  return (
                    <tr key={`row-${globalIdx}`} className="border-b border-gray-200 hover:bg-gray-50 transition-colors">
                      {Object.keys(row).map((key) => (
                        <td key={`${globalIdx}-${key}`} className="px-4 py-3 text-gray-700 max-w-xs truncate">
                          {row[key]}
                        </td>
                      ))}
                      <td className="px-4 py-3">
                        <div className="flex space-x-2">
                          <button
                            onClick={() => {
                              setEditingRowIndex(globalIdx);
                              setEditingRowData({ ...row });
                              setIsEditing(true);
                            }}
                            className="text-[#0098B0] hover:text-[#007a96] p-1.5 rounded hover:bg-blue-50 transition-colors"
                            title="Edit row"
                          >
                            <FontAwesomeIcon icon={faEdit} />
                          </button>
                          <button
                            onClick={() => handleDeleteRow("row", globalIdx)}
                            className="text-red-500 hover:text-red-700 p-1.5 rounded hover:bg-red-50 transition-colors"
                            title="Delete row"
                          >
                            <FontAwesomeIcon icon={faTrash} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {/* Pagination Controls */}
          <div className="flex flex-wrap items-center justify-between mt-4 px-2 py-2">
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600">Rows per page:</span>
              <select
                value={rowsPerPage}
                onChange={e => {
                  setRowsPerPage(Number(e.target.value));
                  setCurrentPage(1);
                }}
                className="border border-gray-300 rounded px-2 py-1 text-sm"
              >
                {[5, 10, 20, 50, 100].map(opt => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                disabled={currentPage === 1}
                className="px-3 py-1.5 rounded bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm disabled:opacity-50"
              >
                Previous
              </button>
              <span className="text-sm text-gray-600">
                Page {currentPage} of {totalPages}
              </span>
              <button
                onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                disabled={currentPage === totalPages}
                className="px-3 py-1.5 rounded bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Form Modal */}
      {isEditing && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
          <div className="bg-white p-6 rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-5">
              <h3 className="text-xl font-bold text-gray-800">
                Editing Row {editingRowIndex + 1}
              </h3>
              <button
                onClick={cancelEdit}
                className="text-gray-500 hover:text-gray-700 p-1 rounded-full hover:bg-gray-100 transition-colors"
              >
                <FontAwesomeIcon icon={faTimes} />
              </button>
            </div>
            <form onSubmit={handleUpdateRow} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-h-96 overflow-y-auto p-1">
                {Object.keys(editingRowData).map((key) => (
                  <div key={key} className="flex flex-col">
                    <label className="text-sm font-medium text-gray-700 mb-1">{key}</label>
                    <input
                      type="text"
                      value={editingRowData[key] || ""}
                      onChange={(e) => setEditingRowData({ ...editingRowData, [key]: e.target.value })}
                      className="border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-[#0098B0]/30 focus:border-[#0098B0] outline-none transition-all"
                    />
                  </div>
                ))}
              </div>
              <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200 mt-6">
                <button
                  type="button"
                  onClick={cancelEdit}
                  className="px-5 py-2.5 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-green-600 text-white px-5 py-2.5 rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2"
                >
                  <FontAwesomeIcon icon={faSave} />
                  <span>Save Changes</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Upload Button */}
      {csvPreview.length > 0 && (
        <button
          onClick={handleUploadCSV}
          className="w-full bg-[#0098B0] text-white py-3 rounded-xl hover:bg-[#007a96] transition-colors flex items-center justify-center space-x-2 font-medium shadow-sm"
        >
          <FontAwesomeIcon icon={faUpload} />
          <span>Upload CSV</span>
        </button>
      )}
    </div>
  );
};

/* ------------------------
   Delete Confirmation Modal
------------------------ */
const DeleteConfirmationModal = ({
  deleteTarget,
  headers,
  headerDeleteConfirm,
  setHeaderDeleteConfirm,
  onConfirm,
  onCancel
}) => {
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
      <div className="bg-white p-6 rounded-2xl shadow-2xl w-full max-w-md">
        <div className="flex items-center mb-4 text-red-500">
          <FontAwesomeIcon icon={faExclamationTriangle} className="text-2xl mr-3" />
          <h3 className="text-xl font-bold">Confirm Deletion</h3>
        </div>

        <p className="text-gray-700 mb-4">
          {deleteTarget.type === "row"
            ? `Are you sure you want to delete row ${deleteTarget.index + 1}? This action cannot be undone.`
            : `Are you sure you want to delete the column "${headers[deleteTarget.index]}"?`}
        </p>

        {deleteTarget.type === "header" && (
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Type <span className="font-mono">"{headers[deleteTarget.index]}"</span> to confirm:
            </label>
            <input
              type="text"
              value={headerDeleteConfirm}
              onChange={(e) => setHeaderDeleteConfirm(e.target.value)}
              className="border border-gray-300 rounded-lg px-4 py-2.5 w-full focus:ring-2 focus:ring-red-300 focus:border-red-500 outline-none transition-all"
              placeholder="Enter column name"
            />
          </div>
        )}

        <div className="flex justify-end space-x-3">
          <button
            onClick={onCancel}
            className="px-5 py-2.5 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="px-5 py-2.5 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center space-x-2"
          >
            <FontAwesomeIcon icon={faTrash} />
            <span>Delete</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default DatasetManager;
/* ------------------------
   Popup Modal Component
------------------------ */
const PopupModal = ({ message, onClose }) => (
  <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
    <div className="bg-white p-6 rounded-2xl shadow-2xl w-full max-w-sm flex flex-col items-center">
      <div className="mb-4 text-center text-lg text-gray-800">{message}</div>
      <button
        onClick={onClose}
        className="bg-[#0098B0] text-white px-6 py-2.5 rounded-lg hover:bg-[#007a96] transition-colors font-medium"
      >
        Close
      </button>
    </div>
  </div>
);