import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Variable } from 'src/app/core/common/variable';

@Component({
  selector: 'app-change',
  templateUrl: './crudvariable.component.html'
})
export class CrudVariableComponent{
 

  VariableArray: Variable[] = [];
  id = 0;
  name = "";
  type = "";
  quantity = 0;
  description = "";

  constructor(private http: HttpClient )
  {
    this.getAllVariable();
  }
 
  saveRecords()
  {
    let bodyData = {
      "name" : this.name,
      "type" : this.type,
      "quantity" : this.quantity
    };
 
    this.http.post("http://127.0.0.1:8000/variable/new",bodyData).subscribe((resultData: any)=>
    {
        console.log(resultData);
        alert("Variable Registered Successfully");
        this.getAllVariable();
    });
  }
 
 
  getAllVariable()
  {
    this.http.get("http://127.0.0.1:8000/variable/getall")
    .subscribe((resultData: any)=>
    {
        console.log(resultData);
        this.VariableArray = resultData;
    });
  }
 
  setUpdate(data: any)
  {
   this.name = data.name;
   this.type = data.type;
   this.quantity = data.quantity;
   this.id = data.id;
   
  }

  UpdateRecords()
  {
    let bodyData = 
    {
      "name" : this.name,
      "type" : this.type,
      "quantity" : this.quantity
    };
    
    this.http.put("http://127.0.0.1:8000/variable/"+ this.id , bodyData).subscribe((resultData: any)=>
    {
        console.log(resultData);
        alert("Variable Registered Updateddd")
        this.name = '';
        this.type = '';
        this.quantity  = 0;
        this.getAllVariable();
    });
  }


  setDelete(data: any)
  {
    this.http.delete("http://127.0.0.1:8000/Variable"+ "/"+ data.id).subscribe((resultData: any)=>
    {
        console.log(resultData);
        alert("Variable Deletedddd")
        this.getAllVariable();
    });
 
  }

}
