import { Component, OnInit, ViewChildren, QueryList } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { Observable } from 'rxjs';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';

import { UntypedFormBuilder, UntypedFormGroup, FormArray, Validators } from '@angular/forms';

import { FolderModel, recentModel } from './file-manager.model';
import { folderData } from './data';
import { Recentervice } from './file-manger.service';
import { NgbdRecentortableHeader, SortEvent } from './file-manager-sortable.directive';

@Component({
  selector: 'app-file-manager',
  templateUrl: './file-manager.component.html',
  styleUrls: ['./file-manager.component.scss'],
  providers: [Recentervice, DecimalPipe]
})

/**
 * FileManager Component
 */
export class FileManagerComponent implements OnInit {

  folderData!: FolderModel[];
  submitted = false;
  folderForm!: UntypedFormGroup;
  folderDatas: any;
  recentForm!: UntypedFormGroup;
  recentDatas: any;
  simpleDonutChart: any;
  public isCollapsed = false;

  // Table data
  recentData!: Observable<recentModel[]>;
  total: Observable<number>;
  @ViewChildren(NgbdRecentortableHeader) headers!: QueryList<NgbdRecentortableHeader>;

  constructor(private modalService: NgbModal, public service: Recentervice, private formBuilder: UntypedFormBuilder) {
    this.recentData = service.Recent$;
    this.total = service.total$;
  }

  ngOnInit(): void {

    document.body.classList.add('file-detail-show');

    /**
     * Form Validation
    */
    this.folderForm = this.formBuilder.group({
      title: ['', [Validators.required]]
    });

    /**
     * Recent Validation
    */
    this.recentForm = this.formBuilder.group({
      ids: [''],
      icon_name: ['', [Validators.required]]
    });

    // Data Get Function
    this._fetchData();

    this._simpleDonutChart('["--vz-info", "--vz-danger", "--vz-primary", "--vz-success"]');

    // Compose Model Hide/Show
    var isShowMenu = false;
    document.querySelectorAll(".file-menu-btn").forEach(function (item) {
      item.addEventListener("click", function (e) {
        e.preventDefault();
        isShowMenu = true;
        document.getElementById('menusidebar')?.classList.add("menubar-show");
      });
    });
    document.querySelector('.chat-wrapper')?.addEventListener('click', function () {
      if (document.querySelector(".file-manager-sidebar")?.classList.contains('menubar-show')) {
        if (!isShowMenu) {
          document.querySelector(".file-manager-sidebar")?.classList.remove("menubar-show");
        }
        isShowMenu = false;
      }
    });
  }

  // Chart Colors Set
  private getChartColorsArray(colors: any) {
    colors = JSON.parse(colors);
    return colors.map(function (value: any) {
      var newValue = value.replace(" ", "");
      if (newValue.indexOf(",") === -1) {
        var color = getComputedStyle(document.documentElement).getPropertyValue(newValue);
        if (color) {
          color = color.replace(" ", "");
          return color;
        }
        else return newValue;;
      } else {
        var val = value.split(',');
        if (val.length == 2) {
          var rgbaColor = getComputedStyle(document.documentElement).getPropertyValue(val[0]);
          rgbaColor = "rgba(" + rgbaColor + "," + val[1] + ")";
          return rgbaColor;
        } else {
          return newValue;
        }
      }
    });
  }

  // Chat Data Fetch
  private _fetchData() {
    // Folder Data Fetch
    this.folderData = folderData;
    this.folderDatas = Object.assign([], this.folderData);

    // Recent Data Fetch
    this.recentData.subscribe(x => {
      this.recentDatas = Object.assign([], x);
    });
  }

  /**
   * Open modal
   * @param content modal content
   */
  openModal(content: any) {
    this.submitted = false;
    this.modalService.open(content, { size: 'md', centered: true });
  }

  /**
  * Form data get
  */
  get form() {
    return this.folderForm.controls;
  }

  /**
  * Save user
  */
  saveFolder() {
    if (this.folderForm.valid) {
      const title = this.folderForm.get('title')?.value;
      const id = 5;
      const files = '349';
      const gb = "4.10";
      this.folderData.push({
        id,
        title,
        files,
        gb
      });
      this.modalService.dismissAll()
    }
    setTimeout(() => {
      this.folderForm.reset();
    }, 2000);
    this.submitted = true
  }

  /**
   * Confirmation mail model
  */
  deleteId: any;
  confirm(content: any, id: any) {
    this.deleteId = id;
    this.modalService.open(content, { centered: true });
  }

  // Delete Data
  deleteData(id: any) {
    document.getElementById('f-' + id)?.remove();
  }

  // Delete Recent Data
  deleteRecentData(id: any) {
    document.getElementById('r-' + id)?.remove();
  }

  // Folder Filter
  folderSearch() {
    var type = (document.getElementById("file-type") as HTMLInputElement).value;
    if (type) {
      this.folderDatas = this.folderData.filter((data: any) => {
        return data.title === type;
      });
    }
    else {
      this.folderDatas = this.folderData
    }
  }

  /**
   * Active Star
   */
  activeMenu(id: any) {
    document.querySelector('.star-' + id)?.classList.toggle('active');
  }

  /**
   * Open Recent modal
   * @param content modal content
   */
  openRecentModal(recentContent: any) {
    this.submitted = false;
    this.modalService.open(recentContent, { size: 'md', centered: true });
  }

  /**
   * Form data get
   */
  get form1() {
    return this.recentForm.controls;
  }

  /**
  * Save user
  */
  saveRecent() {
    if (this.recentForm.valid) {
      if (this.recentForm.get('ids')?.value) {
        this.recentDatas = this.recentDatas.map((data: { id: any; }) => data.id === this.recentForm.get('ids')?.value ? { ...data, ...this.recentForm.value } : data)
      } else {
        const id = 5;
        const icon = 'ri-file-text-fill';
        const icon_color = 'secondary';
        const icon_name = this.recentForm.get('icon_name')?.value;
        const item = '01';
        const size = "0.3 KB";
        const type = "Media";
        const date = "19 Apr, 2022";
        this.recentDatas.push({
          id,
          icon,
          icon_color,
          icon_name,
          item,
          size,
          type,
          date,
        });
        this.modalService.dismissAll();
      }
    }
    this.modalService.dismissAll();
    setTimeout(() => {
      this.recentForm.reset();
    }, 2000);
    this.submitted = true
  }

  /**
   * Open modal
   * @param content modal content
   */
  editModal(recentContent: any, id: any) {
    this.submitted = false;
    this.modalService.open(recentContent, { size: 'md', centered: true });
    var listData = this.recentDatas.filter((data: { id: any; }) => data.id === id);
    this.recentForm.controls['icon_name'].setValue(listData[0].icon_name);
    this.recentForm.controls['ids'].setValue(listData[0].id);
  }

  // OverView Chart
  /**
 * Simple Donut Chart
 */
  private _simpleDonutChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.simpleDonutChart = {
      series: [27.01, 20.87, 33.54, 37.58],
      chart: {
        height: 330,
        type: 'donut',
      },
      legend: {
        position: 'bottom'
      },
      labels: ["Documents", "Media", "Others", "Free Space"],
      dataLabels: {
        dropShadow: {
          enabled: false,
        }
      },
      colors: colors
    };
  }

  /**
 * Open modal
 * @param content modal content
 */
  editdata(id: any) {
    (document.getElementById("file-overview") as HTMLElement).style.display = "block";
    (document.getElementById("folder-overview") as HTMLElement).style.display = "none";
    var data = this.recentDatas.filter((data: { id: any; }) => data.id === id);
    (document.querySelector('#file-overview .file-icon i') as HTMLImageElement).className = data[0].icon + ' ' + 'text-' + data[0].icon_color;
    var file_name: any = document.querySelectorAll('#file-overview .file-name');
    file_name.forEach((name: any) => {
      name.innerHTML = data[0].icon_name
    });
    var file_size: any = document.querySelectorAll('#file-overview .file-size');
    file_size.forEach((name: any) => {
      name.innerHTML = data[0].size
    });
    var create_date: any = document.querySelectorAll('#file-overview .create-date');
    create_date.forEach((name: any) => {
      name.innerHTML = data[0].date
    });
    (document.querySelector('#file-overview .file-type') as HTMLImageElement).innerHTML = data[0].type;
  }

  // Overview Model Close
  closeModel() {
    document.body.classList.remove('file-detail-show');
  }

  /**
  * Product Filtering  
  */
  changeProducts(e: any, name: any) {

    (document.getElementById("folder-list") as HTMLElement).style.display = "none";
    this.recentData.subscribe(x => {
      this.recentDatas = x.filter((product: any) => {
        return product.type === name;
      });
    });
  }

}
