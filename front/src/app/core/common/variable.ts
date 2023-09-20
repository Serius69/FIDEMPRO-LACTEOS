export interface Variable {
  id: number;
  name: string ;
  unit: string ;
  idproduct: number;
  base: string;
  quantity: number;
  description: string;
  status:number;
}
export const variableList: Variable[] = [
  {
      id: 1,
      name: 'Full',
      description: 'Tommy',
      base: '26 Mar, 2021',
      unit: '',
      idproduct: 5.50,
      quantity: 120.40,
      status: 1,
  }
];