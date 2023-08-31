import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-change',
  templateUrl: './change.component.html'
})
export class ChangeComponent{

  VariableArray : any[] = [];
 
  name: string ="";
  address: string ="";
  fee: Number =0;
  description: string ="";
 
  currentVariableID = "";
 
  constructor(private http: HttpClient )
  {
    this.getAllVariable();
  }
 
  saveRecords()
  {
    let bodyData = {
      "name" : this.name,
      "address" : this.address,
      "fee" : this.fee
    };
 
    this.http.post("http://127.0.0.1:8000/product/new",bodyData).subscribe((resultData: any)=>
    {
        console.log(resultData);
        alert("Variable Registered Successfully");
        this.getAllVariable();
    });
  }
 
 
  getAllVariable()
  {
    this.http.get("http://127.0.0.1:8000/product/getall")
    .subscribe((resultData: any)=>
    {
        console.log(resultData);
        this.VariableArray = resultData;
    });
  }
 
  setUpdate(data: any)
  {
   this.name = data.name;
   this.address = data.address;
   this.fee = data.fee;
   this.currentVariableID = data.id;
   
  }

  UpdateRecords()
  {
    let bodyData = 
    {
      "name" : this.name,
      "address" : this.address,
      "fee" : this.fee
    };
    
    this.http.put("http://127.0.0.1:8000/Variable/"+ this.currentVariableID , bodyData).subscribe((resultData: any)=>
    {
        console.log(resultData);
        alert("Variable Registered Updateddd")
        this.name = '';
        this.address = '';
        this.fee  = 0;
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
