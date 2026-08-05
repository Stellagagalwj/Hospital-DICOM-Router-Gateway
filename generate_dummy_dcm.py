import pydicom
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import UID
import datetime

def create_dummy_dicom(filename, modality):
    # 1. 配置文件元数据 (File Meta Information)
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = UID('1.2.840.10008.5.1.4.1.1.2') # 默认用 CT Image Storage
    file_meta.MediaStorageSOPInstanceUID = UID('1.2.3.4.5.6.7')
    file_meta.ImplementationClassUID = UID('1.2.3.4')
    file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian

    # 2. 初始化 DICOM 数据集，必须包含标准的 128 字节空前缀 (preamble)
    ds = FileDataset(filename, {}, file_meta=file_meta, preamble=b"\0" * 128)

    # 3. 填充关键的 DICOM 标签 (Tags)
    ds.PatientName = "Dummy^Patient"
    ds.PatientID = "123456"
    ds.Modality = modality  # 你的网关路由正是依赖这个标签！
    ds.StudyDate = datetime.datetime.now().strftime('%Y%m%d')
    ds.StudyInstanceUID = UID('1.2.3.4.5.6.7.8')
    ds.SeriesInstanceUID = UID('1.2.3.4.5.6.7.8.9')
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.SOPClassUID = file_meta.MediaStorageSOPClassUID

    # 4. 设置字节序并保存为文件
    ds.is_little_endian = True
    ds.is_implicit_VR = False
    ds.save_as(filename)
    print(f"✅ 假 DICOM 文件生成成功：{filename} (被标记为: {modality})")

if __name__ == "__main__":
    # 运行脚本时，自动生成一个 CT 影像和一个 MR (核磁共振) 影像
    create_dummy_dicom("test_scan_CT.dcm", "CT")
    create_dummy_dicom("test_scan_MR.dcm", "MR")