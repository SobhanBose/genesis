import { promises as fs } from "fs";
import Papa from "papaparse";

// List all datasets in backup folder
const listDatasets = async () => {
  const path = "./resources/backup";
  try {
    const files = await fs.readdir(path);
    return {
      success: true,
      fileList: files.map(file => file.replace(".csv", ""))
    };
  } catch (err) {
    console.error("Error reading directory:", err);
    return { success: false, error: err };
  }
};

// Fetch the most recent dataset
const fetchRecentDataset = async () => {
  const path = "./resources/dataset.csv";
  try {
    const ds = await fs.readFile(path, "utf8");
    return { success: true, data: ds };
  } catch (err) {
    console.error("Error reading recent dataset:", err);
    return { success: false, error: err };
  }
};

// Fetch a dataset by name
const fetchDatasetByName = async (name) => {
  const path = `./resources/backup/${name}.csv`;
  try {
    const ds = await fs.readFile(path, "utf8");
    return { success: true, data: ds };
  } catch (err) {
    console.error("Error reading dataset by name:", err);
    return { success: false, error: err };
  }
};

// Override dataset with new row
const overrideRecentDatasetFromRow = async (row) => {
  try {
    const path = "./resources/dataset.csv";
    const file = await fs.readFile(path, "utf8");

    const parsed = Papa.parse(file, { header: true, skipEmptyLines: true });
    parsed.data.push(row);

    const newDataset = Papa.unparse(parsed.data, { header: false });
    await fs.writeFile(path, newDataset);

    return { success: true };
  } catch (err) {
    console.error("Error overriding dataset:", err);
    return { success: false, error: err };
  }
};

// append dataset with new CSV content
const appendRecentDatasetFromCSV = async (parsed) => {
  try {
    const path = "./resources/dataset.csv";
    const newCsv = Papa.unparse(parsed.data, { header: false });
    await fs.appendFile(path, "\n" + newCsv);
    return { success: true };

  } catch (err) {
    console.error("Error overriding dataset:", err);
    return { success: false, error: err };
  }
};


// Delete dataset by name
const deleteDatasetByName = async (name) => {
  try {
    const path = `./resources/backup/${name}.csv`;
    await fs.unlink(path);
    return { success: true };
  } catch (err) {
    console.error("Error deleting file:", err);
    return { success: false, error: err };
  }
};

// Move recent dataset into backup folder with timestamp
const changeRecentDatasetDirectoryToBackup = async () => {
  try {
    const oldPath = "./resources/dataset.csv";
    const newPath = `./resources/backup/${Date.now()}.csv`;
    await fs.rename(oldPath, newPath);
    return { success: true };
  } catch (err) {
    console.error("Error moving file:", err);
    return { success: false, error: err };
  }
};

// Create new dataset file
const createNewRecentDataset = async () => {
  try {
    const path = "./resources/dataset.csv";
    const headers = ["chr","start","end","ref","alt","class","gene","phastconselements100way","phylop100way_vertebrate","phylop20way_mammalian","phastcons100way_vertebrate","phastcons20way_mammalian","siphy_29way_logodds","phylop30way_mammalian","phastcons30way_mammalian","af","af_raw","af_male","af_female","af_afr","af_ami","af_amr","af_asj","af_eas","af_fin","af_nfe","af_oth","gdi","gdi_phred","rvis1","rvis2","lof_score","molecular_weight","equipotential_point","hydrophilic","hydrophobic","amphipathic_","cyclic","essential","aromatic","aliphatic","nonpolar","polar_uncharged","acidic","basic","sulfur","pka_cooh","pka_nh3","blosum100","ds_ag","ds_al","ds_dg","ds_dl","dp_ag","dp_al","dp_dg","dp_dl","gm12878","h1hesc","hepg2","hmec","hsmm","huvec","k562","nhek","nhlf","func_frameshift","func_nonframeshift","func_nonsynonymous_snv","func_startloss","func_stopgain","func_stoploss","omim_autosomal_dominant","omim_autosomal_recessive","omim_x_linked_dominant","omim_x_linked_recessive","omim_other"].join(",");

    await fs.writeFile(path, headers);
    return { success: true };

  } catch (err) {
    console.error("Error creating file:", err);
    return { success: false, error: err };
  }
}

export {
  listDatasets,
  fetchRecentDataset,
  fetchDatasetByName,
  overrideRecentDatasetFromRow,
  appendRecentDatasetFromCSV,
  deleteDatasetByName,
  changeRecentDatasetDirectoryToBackup,
  createNewRecentDataset
};
