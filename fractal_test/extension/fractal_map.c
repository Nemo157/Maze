#include <Python.h>
#include "structmember.h"
#include <stdlib.h>
#include <float.h>

static const double pi = 3.14159265358979323846264338327950288419716939937510;

typedef struct {
  int small[10];
  int big1;
  int big2;
  int big3;
} Perlin;

typedef struct {
  PyObject_HEAD
  int octaves;
  float persistence;
  Perlin *perlins;
} FractalMap;



Perlin new_perlin() {
  Perlin perlin;
  int i;
  int smalls[] = {547, 557, 563, 569, 571, 577, 587, 593, 599, 601};

  srand((unsigned int)time(NULL));
  for (i = 0; i < 10; i++){
    perlin.small[i] = smalls[i];
  }
  perlin.big1 = (rand() % 32767) + 10000; // 32 767 - 42 767
  perlin.big2 = (rand() % 32767) * (rand() % 8) + 750000; // 262 136 - 1 012 136
  perlin.big3 = (rand() % 32767) * (rand() % 15259) + 1000000000; // 499 991 653 - 1 499 991 653
  return perlin;
}

// Crap randomiser, need to find something with less repetition
// Works okay for fractal generation though
static double noise(int *x, int size, Perlin *settings) {
    int i;
    int n = 0;
    for (i = 0; i < size; i++) {
      n += x[i] * settings->small[i];
    }
    n = (n<<13) ^ n;
    return ( 1.0 - ( (n * (n * n * settings->big1 + settings->big2) + settings->big3) & 0x7fffffff) / 1073741824.0);
  }

static double smooth(int *x, int size, Perlin *settings) {
    double value = 0.0;
    if (size == 1) {
      x[0] -= 1; value += noise(x, 1, settings);
      x[0] += 2; value += noise(x, 1, settings);
      value /= 2;
      x[0] -= 1; value += noise(x, 1, settings);
      value /= 2;
    }
    else if (size == 2) {
      x[0] -= 1; value += noise(x, 2, settings);
      x[0] += 2; value += noise(x, 2, settings);
      x[0] -= 1;
      x[1] -= 1; value += noise(x, 2, settings);
      x[1] += 2; value += noise(x, 2, settings);
      x[1] -= 1;
      value *= 3;
      x[1] -= 1;
      x[0] -= 1; value += noise(x, 2, settings);
      x[0] += 2; value += noise(x, 2, settings);
      x[1] += 2;
      x[0] -= 2; value += noise(x, 2, settings);
      x[0] += 2; value += noise(x, 2, settings);
      value /= 16;
      x[0] -= 1; x[1] -= 1;
      value += noise(x, 2, settings);
      value /= 2;
    }
    else {
      value = noise(x, size, settings);
    }
    return value;
  }

static double int_f(int *y, double *x, int *fx, int *cx, int size, int depth, Perlin *settings) {
  double x1, x2, f;
  if (size - depth == 0)
    return smooth(y, size, settings);
  y[depth] = fx[depth];
  x1 = int_f(y, x, fx, cx, size, depth + 1, settings);
  y[depth] = cx[depth];
  x2 = int_f(y, x, fx, cx, size, depth + 1, settings);
  f = (1 - cos(pi*(x[depth] - fx[depth]))) / 2;
  return x1 * (1 - f) + x2 * f;
}

static double interpolated(double *x, int size, Perlin *settings) {
  int *fx,*cx, *y, i;
  double value;
  
  fx = malloc(size * sizeof(int));
  cx = malloc(size * sizeof(int));
  y = malloc(size * sizeof(int));
  
  if (! (y && fx && cx)) {
    // Error
  }
  for (i = 0; i < size; i++) {
    fx[i] = (int)floor(x[i]);
    cx[i] = fx[i] + 1;
  }
  value = int_f(y, x, fx, cx, size, 0, settings);
  free(fx); free(cx); free(y);
  return value;
}

static PyObject * value(PyObject *self1, PyObject *args) {
  int i, j, size = 6;
  double x[10] = {FLT_MAX, FLT_MAX, FLT_MAX, FLT_MAX, FLT_MAX, FLT_MAX, FLT_MAX, FLT_MAX, FLT_MAX, FLT_MAX}; /* Currently max 10-dimensional values. */
  double output = 0.0;
  FractalMap *self;
  
  self = (FractalMap *)self1;
  
  if (!PyArg_ParseTuple(args, "d|ddddddddd", &x[0], &x[1], &x[2], &x[3], &x[4], &x[5], &x[6], &x[7], &x[8], &x[9]))
    return NULL;
  
  for (i = 9; i >= 0; i--) if (x[i] < FLT_MAX) { size = i + 1; break; }
  
  
  for (i = 0; i < self->octaves; i++) {
    output += pow(self->persistence, (self->octaves - i - 1)) * interpolated(x, size, &self->perlins[i]);
    for (j = 0; j < size; j++) { x[j] /= 2; }
  }
  
  return Py_BuildValue("d", output);
}

static PyObject * __getitem__(PyObject *self, PyObject *args) {
    return value(self, args);
}

static PyMethodDef FractalMap_methods[] = {
  {"value", value, METH_VARARGS, ""},
  {"__getitem__", __getitem__, METH_VARARGS, ""},
  {NULL, NULL, 0, NULL} /* Sentinel */
};

static PyMemberDef FractalMap_members[] = {
  {"octaves", T_INT, offsetof(FractalMap, octaves), READONLY, "number of octaves"},
  {"persistence", T_FLOAT, offsetof(FractalMap, persistence), READONLY, "persistence"},
  {NULL}  /* Sentinel */
};

static PyMappingMethods FractalMap_mappingMethods[] = {
  {NULL, __getitem__, NULL}
};

static void
FractalMap_dealloc(FractalMap* self) {
  free(self->perlins);
  self->ob_type->tp_free((PyObject*)self);
}

static int
FractalMap_init(FractalMap *self, PyObject *args, PyObject *kwds) {
  int i;

  if (! PyArg_ParseTuple(args, "if", &self->octaves, &self->persistence))
    return -1;
  
  self->perlins = malloc(self->octaves * sizeof(Perlin));
  if (!self->perlins)
    return -1;
  
  for (i = 0; i < self->octaves; i++){
    self->perlins[i] = new_perlin();
  }
  
  return 0;
}



static PyTypeObject FractalMapType = {
  PyObject_HEAD_INIT(NULL)
  0,                         /*ob_size*/
  "fractal_map.FractalMap",             /*tp_name*/
  sizeof(FractalMap), /*tp_basicsize*/
  0,                         /*tp_itemsize*/
  (destructor)FractalMap_dealloc,                         /*tp_dealloc*/
  0,                         /*tp_print*/
  0,                         /*tp_getattr*/
  0,                         /*tp_setattr*/
  0,                         /*tp_compare*/
  0,                         /*tp_repr*/
  0,                         /*tp_as_number*/
  0,                         /*tp_as_sequence*/
  FractalMap_mappingMethods,                         /*tp_as_mapping*/
  0,                         /*tp_hash */
  0,                         /*tp_call*/
  0,                         /*tp_str*/
  0,                         /*tp_getattro*/
  0,                         /*tp_setattro*/
  0,                         /*tp_as_buffer*/
  Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,        /*tp_flags*/
  "Fractal Map",           /* tp_doc */
  0,                   /* tp_traverse */
  0,                 /* tp_clear */
  0,                 /* tp_richcompare */
  0,                     /* tp_weaklistoffset */
  0,                 /* tp_iter */
  0,                 /* tp_iternext */
  FractalMap_methods,             /* tp_methods */
  FractalMap_members,             /* tp_members */
  0,                         /* tp_getset */
  0,                         /* tp_base */
  0,                         /* tp_dict */
  0,                         /* tp_descr_get */
  0,                         /* tp_descr_set */
  0,                         /* tp_dictoffset */
  (initproc)FractalMap_init,      /* tp_init */
  0,                         /* tp_alloc */
};

#ifndef PyMODINIT_FUNC	/* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif
PyMODINIT_FUNC
initfractal_map(void) {
  PyObject* m;

  FractalMapType.tp_new = PyType_GenericNew;
  if (PyType_Ready(&FractalMapType) < 0)
      return;

  m = Py_InitModule3("fractal_map", FractalMap_methods,"");

  Py_INCREF(&FractalMapType);
  PyModule_AddObject(m, "FractalMap", (PyObject *)&FractalMapType);
}



int main(int argc, char *argv[]) {
  /* Pass argv[0] to the Python interpreter */
    Py_SetProgramName(argv[0]);

    /* Initialize the Python interpreter.  Required. */
    Py_Initialize();

    /* Add a static module */
    initfractal_map();
    
    return 0;
}
