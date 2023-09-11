import { Component, OnInit, ViewChild, TemplateRef, ChangeDetectorRef } from '@angular/core';

// Calendar option
import { CalendarOptions, DateSelectArg, EventClickArg, EventApi } from '@fullcalendar/core';
import interactionPlugin from '@fullcalendar/interaction';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import listPlugin from '@fullcalendar/list';
import { EventInput } from '@fullcalendar/core';

// BootStrap
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { UntypedFormBuilder, Validators, UntypedFormGroup } from '@angular/forms';
// Sweet Alert
import Swal from 'sweetalert2';

// Calendar Services
import { restApiService } from "../../../core/services/rest-api.service";

import { category, calendarEvents, createEventId } from './data';
import { DatePipe } from '@angular/common';

@Component({
  selector: 'app-calendar',
  templateUrl: './calendar.component.html',
  styleUrls: ['./calendar.component.scss']
})

/**
 * Calendar Component
 */
export class CalendarComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;

  // calendar
  calendarEvents!: EventInput[];
  editEvent: any;
  formEditData!: UntypedFormGroup;
  newEventDate: any;
  category!: any[];
  submitted = false;

  // Calendar click Event
  formData!: UntypedFormGroup;
  @ViewChild('editmodalShow') editmodalShow!: TemplateRef<any>;
  @ViewChild('modalShow') modalShow !: TemplateRef<any>;

  constructor(private modalService: NgbModal, private formBuilder: UntypedFormBuilder, private changeDetector: ChangeDetectorRef,
    private datePipe: DatePipe, private restApiService: restApiService) { }

  ngOnInit(): void {
    /**
     * BreadCrumb
     */
    this.breadCrumbItems = [
      { label: 'Apps' },
      { label: 'Calendar', active: true }
    ];

    // Validation
    this.formData = this.formBuilder.group({
      title: ['', [Validators.required]],
      category: ['', [Validators.required]],
      location: ['', [Validators.required]],
      description: ['', [Validators.required]],
      date: ['', Validators.required],
      start: ['', Validators.required],
      end: ['', Validators.required]
    });

    this._fetchData();
  }

  /**
   * Fetches the data
   */
  private _fetchData() {
    // Event category
    this.category = category;

    // Calender Event Data
    // this.calendarEvents = calendarEvents; 
    this.restApiService.getCalendarData().subscribe(
      data => {
        const users = JSON.parse(data);
        this.calendarEvents = users.data;
        this.calendarOptions.initialEvents = this.calendarEvents.map(
          (evt: any) => {
            return { date: evt.start, title: evt.title, className: evt.className, location: evt.location, description: evt.description }
          })
      });
  }

  /***
  * Calender Set
  */
  calendarOptions: CalendarOptions = {
    plugins: [
      interactionPlugin,
      dayGridPlugin,
      timeGridPlugin,
      listPlugin,
    ],
    headerToolbar: {
      left: 'dayGridMonth,dayGridWeek,dayGridDay',
      center: 'title',
      right: 'prevYear,prev,next,nextYear'
    },
    initialView: "dayGridMonth",
    themeSystem: "bootstrap",
    initialEvents: this.calendarEvents || calendarEvents,
    weekends: true,
    editable: true,
    selectable: true,
    selectMirror: true,
    dayMaxEvents: true,
    select: this.openModal.bind(this),
    eventClick: this.handleEventClick.bind(this),
    eventsSet: this.handleEvents.bind(this),
  };
  currentEvents: EventApi[] = [];

  /**
   * Event add modal
   */
  openModal(event?: any) {
    this.submitted = false;
    this.newEventDate = event,
      this.formBuilder.group({
        editDate: this.newEventDate.date
      })
    this.modalService.open(this.modalShow, { centered: true });
  }

  /**
   * Event click modal show
   */
  handleEventClick(clickInfo: EventClickArg) {
    this.editEvent = clickInfo.event;

    this.formEditData = this.formBuilder.group({
      editTitle: clickInfo.event.title,
      editCategory: clickInfo.event.classNames[0],
      editlocation: clickInfo.event.extendedProps['location'],
      editDescription: clickInfo.event.extendedProps['description'],
      editDate: clickInfo.event.start,
      editStart: clickInfo.event.start,
      editEnd: clickInfo.event.end
    });
    this.modalService.open(this.editmodalShow, { centered: true });
  }

  /**
   * Events bind in calander
   * @param events events
   */
  handleEvents(events: EventApi[]) {

    this.currentEvents = events;
    // this.changeDetector.detectChanges();
  }

  /**
   * Close event modal
   */
  closeEventModal() {
    this.formData = this.formBuilder.group({
      title: '',
      category: '',
      location: '',
      description: '',
      date: '',
      start: '',
      end: ''
    });
    this.modalService.dismissAll();
  }

  /***
   * Model Position Set
   */
  position() {
    Swal.fire({
      position: 'center',
      icon: 'success',
      title: 'Event has been saved',
      showConfirmButton: false,
      timer: 1000,
    });
  }

  /***
   * Model Edit Position Set
   */
  Editposition() {
    Swal.fire({
      position: 'center',
      icon: 'success',
      title: 'Event has been Updated',
      showConfirmButton: false,
      timer: 1000,
    });
  }

  /**
   * Event Data Get
   */
  get form() {
    return this.formData.controls;
  }

  /**
   * Save the event
   */
  saveEvent() {
    if (this.formData.valid) {
      const className = this.formData.get('category')!.value;
      const title = this.formData.get('title')!.value;
      const location = this.formData.get('location')!.value;
      const description = this.formData.get('description')!.value
      const date = this.formData.get('date')!.value
      const starttime = this.formData.get('start')!.value;
      const endtime = this.formData.get('end')!.value;
      const yy = new Date(date).getFullYear();
      const mm = new Date(date).getMonth() + 1;
      const dd = new Date(date).getDate();

      const start = new Date(mm + '-' + dd + '-' + yy);
      start.setHours((starttime.split(' ')[0]).split(':')[0]);
      start.setMinutes((starttime.split(' ')[0]).split(':')[1]);

      const end = new Date(mm + '-' + dd + '-' + yy);
      end.setHours((endtime.split(' ')[0]).split(':')[0]);
      end.setMinutes((endtime.split(' ')[0]).split(':')[1]);
      const calendarApi = this.newEventDate.view.calendar;

      calendarApi.addEvent({
        id: createEventId(),
        title,
        date,
        start,
        end,
        location,
        description,
        className: className + ' ' + 'text-white'
      });
      this.position();
      this.formData = this.formBuilder.group({
        title: '',
        category: '',
        location: '',
        description: '',
        date: '',
        start: '',
        end: ''
      });
      this.modalService.dismissAll();
      this.submitted = true;
    } else {
    }
  }

  /**
   * save edit event data
   */
  editEventSave() {

    const editTitle = this.formEditData.get('editTitle')!.value;
    const editCategory = this.formEditData.get('editCategory')!.value;
    const editdate = this.formEditData.get('editDate')!.value;
    const editstart = this.formEditData.get('editDate')!.value;
    const editend = this.formEditData.get('editEnd')!.value;
    const editlocation = this.formEditData.get('editlocation')!.value;
    const editdescription = this.formEditData.get('editDescription')!.value;

    const editId = this.calendarEvents.findIndex(
      (x) => x.id + '' === this.editEvent.id + ''
    );

    this.editEvent.setProp('title', editTitle);
    this.editEvent.setProp('classNames', editCategory);
    this.editEvent.setProp('date', editdate);
    this.editEvent.setProp('start', editdate);
    this.editEvent.setProp('end', editend);
    this.editEvent.setProp('location', editlocation);
    this.editEvent.setProp('description', editdescription);

    this.calendarEvents[editId] = {
      // ...this.editEvent,
      allDay: false,
      title: editTitle,
      id: this.editEvent.id,
      classNames: editCategory + ' ' + 'text-white',
      start: editstart,
    };
    this.Editposition();
    this.formEditData = this.formBuilder.group({
      editTitle: '',
      editCategory: '',
    });
    this.modalService.dismissAll();
  }

  /**
   * Delete-confirm
   */
  confirm() {
    Swal.fire({
      title: 'Are you sure?',
      text: 'You won\'t be able to revert this!',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#34c38f',
      cancelButtonColor: '#f46a6a',
      confirmButtonText: 'Yes, delete it!',
    }).then((result) => {
      if (result.value) {
        this.deleteEventData();
        Swal.fire('Deleted!', 'Event has been deleted.', 'success');
      }
    });
  }

  /**
   * Delete event
   */
  deleteEventData() {
    this.editEvent.remove();
    this.modalService.dismissAll();
  }


}
