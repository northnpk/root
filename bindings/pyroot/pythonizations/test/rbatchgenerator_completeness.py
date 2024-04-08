import unittest
import os
import ROOT
import numpy as np
import math

class RBatchGeneratorMultipleFiles(unittest.TestCase):

    file_name1 = "first_half.root"
    file_name2 = "second_half.root"
    tree_name = "mytree"

    # default constants
    n_train_batch = 2
    n_val_batch = 1
    val_remainder = 1
    
    # Helpers
    def define_rdf(self, num_of_entries=10):
        df = ROOT.RDataFrame(num_of_entries)\
            .Define("b1", "(int) rdfentry_")\
            .Define("b2", "(double) b1*b1")
        
        return df

    def create_file(self, num_of_entries=10):
        self.define_rdf(num_of_entries).Snapshot(self.tree_name, self.file_name1)
    
    def create_5_entries_file(self):
        df1 = ROOT.RDataFrame(5)\
            .Define("b1", "(int) rdfentry_ + 10")\
            .Define("b2", "(double) b1 * b1")\
            .Snapshot(self.tree_name, self.file_name2)

    def teardown_file(self, file):
        os.remove(file)
    
    def size_of_remainders(self, num_of_entries=10, batch_size=3, chunk_size=5, validation_split=0.3):
        val_remainder = ((num_of_entries // chunk_size) * math.ceil(chunk_size * validation_split))\
            + math.ceil((num_of_entries % chunk_size) * validation_split)
        train_remainder = num_of_entries - val_remainder
        n_of_train_batches = train_remainder // batch_size
        n_of_val_batches = val_remainder // batch_size
        val_remainder %= batch_size
        train_remainder %= batch_size

        return n_of_train_batches, n_of_val_batches, train_remainder, val_remainder


    def test01_each_element_is_generated_unshuffled(self):
        self.create_file()

        gen_train, gen_validation = ROOT.TMVA.Experimental.CreateNumPyGenerators(
        batch_size=3,
        chunk_size=5,
        tree_name=self.tree_name,
        file_names=self.file_name1,
        target="b2",
        validation_split=0.3,
        shuffle=False,
        drop_remainder=False
        )

        results_x_train = [2.0, 3.0, 4.0, 7.0, 8.0, 9.0]
        results_x_val = [0.0, 1.0, 5.0, 6.0]
        results_y_train = [4.0, 9.0, 16.0, 49.0, 64.0, 81.0]
        results_y_val = [0.0, 1.0, 25.0, 36.0]
        
        collected_x_train = []
        collected_x_val = []
        collected_y_train = []
        collected_y_val = []

        for _ in range(self.n_train_batch):
            x, y = next(gen_train)
            self.assertTrue(x.shape==(3,1))
            self.assertTrue(y.shape==(3,1))
            collected_x_train.append(x.tolist())
            collected_y_train.append(y.tolist())
        

        for _ in range(self.n_val_batch):
            x, y = next(gen_validation)
            self.assertTrue(x.shape==(3,1))
            self.assertTrue(y.shape==(3,1))
            collected_x_val.append(x.tolist())
            collected_y_val.append(y.tolist())
        
        x, y = next(gen_validation)
        self.assertTrue(x.shape==(self.val_remainder,1))
        self.assertTrue(y.shape==(self.val_remainder,1))
        collected_x_val.append(x.tolist())
        collected_y_val.append(y.tolist())

        flat_x_train = [x for xl in collected_x_train for xs in xl for x in xs]
        flat_x_val = [x for xl in collected_x_val for xs in xl for x in xs]
        flat_y_train = [y for yl in collected_y_train for ys in yl for y in ys]
        flat_y_val = [y for yl in collected_y_val for ys in yl for y in ys]
        
        self.assertEqual(results_x_train, flat_x_train)
        self.assertEqual(results_x_val, flat_x_val)
        self.assertEqual(results_y_train, flat_y_train)
        self.assertEqual(results_y_val, flat_y_val)

        self.teardown_file(self.file_name1)

    def test02_each_element_is_generated_shuffled(self):
        df = self.define_rdf()

        gen_train, gen_validation = ROOT.TMVA.Experimental.CreateNumPyGenerators(
        batch_size=3,
        chunk_size=5,
        rdataframe=df,
        target="b2",
        validation_split=0.3,
        shuffle=True,
        drop_remainder=False
        )
        
        collected_x_train = []
        collected_x_val = []
        collected_y_train = []
        collected_y_val = []

        for _ in range(self.n_train_batch):
            x, y = next(gen_train)
            self.assertTrue(x.shape==(3,1))
            self.assertTrue(y.shape==(3,1))
            collected_x_train.append(x.tolist())
            collected_y_train.append(y.tolist())

        for _ in range(self.n_val_batch):
            x, y = next(gen_validation)
            self.assertTrue(x.shape==(3,1))
            self.assertTrue(y.shape==(3,1))
            collected_x_val.append(x.tolist())
            collected_y_val.append(y.tolist())
        
        x, y = next(gen_validation)
        self.assertTrue(x.shape==(self.val_remainder,1))
        self.assertTrue(y.shape==(self.val_remainder,1))
        collected_x_val.append(x.tolist())
        collected_y_val.append(y.tolist())

        flat_x_train = {x for xl in collected_x_train for xs in xl for x in xs}
        flat_x_val = {x for xl in collected_x_val for xs in xl for x in xs}
        flat_y_train = {y for yl in collected_y_train for ys in yl for y in ys}
        flat_y_val = {y for yl in collected_y_val for ys in yl for y in ys}
        
        self.assertEqual(len(flat_x_train),6)
        self.assertEqual(len(flat_x_val),4)
        self.assertEqual(len(flat_y_train),6)
        self.assertEqual(len(flat_y_val),4)

    def test03_next_iteration(self):
        df = self.define_rdf()

        gen_train, gen_validation = ROOT.TMVA.Experimental.CreateNumPyGenerators(
        batch_size=3,
        chunk_size=5,
        rdataframe=df,
        target="b2",
        validation_split=0.3,
        shuffle=False,
        drop_remainder=False
        )

        results_x_train = [2.0, 3.0, 4.0, 7.0, 8.0, 9.0]
        results_x_val = [0.0, 1.0, 5.0, 6.0]
        results_y_train = [4.0, 9.0, 16.0, 49.0, 64.0, 81.0]
        results_y_val = [0.0, 1.0, 25.0, 36.0]
        
        collected_x_train = []
        collected_x_val = []
        collected_y_train = []
        collected_y_val = []

        print("Training")
        while True:
            try:
                x, y = next(gen_train)
                self.assertTrue(x.shape==(3,1) or x.shape==(1,1))
                self.assertTrue(y.shape==(3,1) or y.shape==(1,1))
                collected_x_train.append(x.tolist())
                collected_y_train.append(y.tolist())
            except StopIteration:
                break
        
        print("Validation")
        while True:
            try:
                x, y = next(gen_validation)
                self.assertTrue(x.shape==(3,1) or x.shape==(1,1))
                self.assertTrue(y.shape==(3,1) or y.shape==(1,1))
                collected_x_val.append(x.tolist())
                collected_y_val.append(y.tolist())
            except StopIteration:
                break


        flat_x_train = [x for xl in collected_x_train for xs in xl for x in xs]
        flat_x_val = [x for xl in collected_x_val for xs in xl for x in xs]
        flat_y_train = [y for yl in collected_y_train for ys in yl for y in ys]
        flat_y_val = [y for yl in collected_y_val for ys in yl for y in ys]
        
        self.assertEqual(results_x_train, flat_x_train)
        self.assertEqual(results_x_val, flat_x_val)
        self.assertEqual(results_y_train, flat_y_train)
        self.assertEqual(results_y_val, flat_y_val)
    
    def test04_chunk_input_smaller_than_batch_size(self):
        """Checking for the situation when the batch can only be created after
        more than two chunks. If not, segmentation fault will arise"""
        df = self.define_rdf()

        gen_train, gen_validation = ROOT.TMVA.Experimental.CreateNumPyGenerators(
        batch_size=3,
        chunk_size=3,
        rdataframe=df,
        target="b2",
        validation_split=0.6,
        shuffle=False,
        drop_remainder=False
        )

        next(gen_train)
    
    def test05_dropping_remainder(self):
        df = self.define_rdf()

        gen_train, gen_validation = ROOT.TMVA.Experimental.CreateNumPyGenerators(
        batch_size=3,
        chunk_size=5,
        rdataframe=df,
        target="b2",
        validation_split=0.3,
        shuffle=False,
        drop_remainder=True
        )
        
        collected_x = []
        collected_y = []

        for x, y in gen_train:
            self.assertTrue(x.shape==(3,1))
            self.assertTrue(y.shape==(3,1))
            collected_x.append(x)
            collected_y.append(y)
        
        for x, y in gen_validation:
            self.assertTrue(x.shape==(3,1))
            self.assertTrue(y.shape==(3,1))
            collected_x.append(x)
            collected_y.append(y)

        self.assertEqual(len(collected_x), 3)
        self.assertEqual(len(collected_y), 3)
    
    def test06_more_than_one_file(self):
        self.create_file()
        self.create_5_entries_file()

        gen_train, gen_validation = ROOT.TMVA.Experimental.CreateNumPyGenerators(
        batch_size=3,
        chunk_size=5,
        tree_name=self.tree_name,
        file_names=[self.file_name1, self.file_name2],
        target="b2",
        validation_split=0.3,
        shuffle=False,
        drop_remainder=False
        )

        results_x_train = [2.0, 3.0, 4.0, 7.0, 8.0, 9.0, 12.0, 13.0, 14.0]
        results_x_val = [0.0, 1.0, 5.0, 6.0, 10.0, 11.0]
        results_y_train = [4.0, 9.0, 16.0, 49.0, 64.0, 81.0, 144.0, 169.0, 196.0]
        results_y_val = [0.0, 1.0, 25.0, 36.0, 100.0, 121.0]
        
        collected_x_train = []
        collected_x_val = []
        collected_y_train = []
        collected_y_val = []

        for x, y in gen_train:
            self.assertTrue(x.shape==(3,1))
            self.assertTrue(y.shape==(3,1))
            collected_x_train.append(x.tolist())
            collected_y_train.append(y.tolist())
        
        for x, y in gen_validation:
            self.assertTrue(x.shape==(3,1))
            self.assertTrue(y.shape==(3,1))
            collected_x_val.append(x.tolist())
            collected_y_val.append(y.tolist())

        flat_x_train = [x for xl in collected_x_train for xs in xl for x in xs]
        flat_x_val = [x for xl in collected_x_val for xs in xl for x in xs]
        flat_y_train = [y for yl in collected_y_train for ys in yl for y in ys]
        flat_y_val = [y for yl in collected_y_val for ys in yl for y in ys]
        
        self.assertEqual(results_x_train, flat_x_train)
        self.assertEqual(results_x_val, flat_x_val)
        self.assertEqual(results_y_train, flat_y_train)
        self.assertEqual(results_y_val, flat_y_val)

        self.teardown_file(self.file_name1)
        self.teardown_file(self.file_name2)
    
    def test07_multiple_target_columns(self):
        df = ROOT.RDataFrame(10)\
            .Define("b1", "(Short_t) rdfentry_")\
            .Define("b2", "(UShort_t) b1 * b1")\
            .Define("b3", "(double) rdfentry_ * 10")\
            .Define("b4", "(double) b3 * 10")
        
        gen_train, gen_validation = ROOT.TMVA.Experimental.CreateNumPyGenerators(
        batch_size=3,
        chunk_size=5,
        rdataframe=df,
        target=["b2","b4"],
        weights="b3",
        validation_split=0.3,
        shuffle=False,
        drop_remainder=False
        )
        
        results_x_train = [2.0, 3.0, 4.0, 7.0, 8.0, 9.0]
        results_x_val = [0.0, 1.0, 5.0, 6.0]
        results_y_train = [4.0, 200.0, 9.0, 300.0, 16.0, 400.0, 49.0, 700.0, 64.0, 800.0, 81.0, 900.0]
        results_y_val = [0.0, 0.0, 1.0, 100.0, 25.0, 500.0, 36.0, 600.0]
        results_z_train = [20.0, 30.0, 40.0, 70.0, 80.0, 90.0]
        results_z_val = [0.0, 10.0, 50.0, 60.0]

        collected_x_train = []
        collected_x_val = []
        collected_y_train = []
        collected_y_val = []
        collected_z_train = []
        collected_z_val = []

        for _ in range(self.n_train_batch):
            x, y, z = next(gen_train)
            self.assertTrue(x.shape==(3,1))
            self.assertTrue(y.shape==(3,2))
            self.assertTrue(z.shape==(3,1))
            collected_x_train.append(x.tolist())
            collected_y_train.append(y.tolist())
            collected_z_train.append(z.tolist())
        
        for _ in range(self.n_val_batch):
            x, y, z = next(gen_validation)
            self.assertTrue(x.shape==(3,1))
            self.assertTrue(y.shape==(3,2))
            self.assertTrue(z.shape==(3,1))
            collected_x_val.append(x.tolist())
            collected_y_val.append(y.tolist())
            collected_z_val.append(z.tolist())
        
        x, y, z = next(gen_validation)
        self.assertTrue(x.shape==(self.val_remainder,1))
        self.assertTrue(y.shape==(self.val_remainder,2))
        self.assertTrue(z.shape==(self.val_remainder,1))
        collected_x_val.append(x.tolist())
        collected_y_val.append(y.tolist())
        collected_z_val.append(z.tolist())

        flat_x_train = [x for xl in collected_x_train for xs in xl for x in xs]
        flat_x_val = [x for xl in collected_x_val for xs in xl for x in xs]
        flat_y_train = [y for yl in collected_y_train for ys in yl for y in ys]
        flat_y_val = [y for yl in collected_y_val for ys in yl for y in ys]
        flat_z_train = [z for zl in collected_z_train for zs in zl for z in zs]
        flat_z_val = [z for zl in collected_z_val for zs in zl for z in zs]

        self.assertEqual(results_x_train, flat_x_train)
        self.assertEqual(results_x_val, flat_x_val)
        self.assertEqual(results_y_train, flat_y_train)
        self.assertEqual(results_y_val, flat_y_val)
        self.assertEqual(results_z_train, flat_z_train)
        self.assertEqual(results_z_val, flat_z_val)

    def test08_multiple_input_columns(self):
        df = ROOT.RDataFrame(10)\
            .Define("b1", "(Short_t) rdfentry_")\
            .Define("b2", "(UShort_t) b1 * b1")\
            .Define("b3", "(double) rdfentry_ * 10")\
        
        gen_train, gen_validation = ROOT.TMVA.Experimental.CreateNumPyGenerators(
        batch_size=3,
        chunk_size=5,
        rdataframe=df,
        target="b2",
        validation_split=0.3,
        shuffle=False,
        drop_remainder=False
        )
        
        results_x_train = [2.0, 20.0, 3.0, 30.0, 4.0, 40.0, 7.0, 70.0, 8.0, 80.0, 9.0, 90.0]
        results_x_val = [0.0, 0.0, 1.0, 10.0, 5.0, 50.0, 6.0, 60.0]
        results_y_train = [4.0, 9.0, 16.0, 49.0, 64.0, 81.0]
        results_y_val = [0.0, 1.0, 25.0, 36.0]

        collected_x_train = []
        collected_x_val = []
        collected_y_train = []
        collected_y_val = []

        for _ in range(self.n_train_batch):
            x, y = next(gen_train)
            self.assertTrue(x.shape==(3,2))
            self.assertTrue(y.shape==(3,1))
            collected_x_train.append(x.tolist())
            collected_y_train.append(y.tolist())

        
        for _ in range(self.n_val_batch):
            x, y = next(gen_validation)
            self.assertTrue(x.shape==(3,2))
            self.assertTrue(y.shape==(3,1))
            collected_x_val.append(x.tolist())
            collected_y_val.append(y.tolist())
        
        x, y = next(gen_validation)
        self.assertTrue(x.shape==(self.val_remainder,2))
        self.assertTrue(y.shape==(self.val_remainder,1))
        collected_x_val.append(x.tolist())
        collected_y_val.append(y.tolist())

        flat_x_train = [x for xl in collected_x_train for xs in xl for x in xs]
        flat_x_val = [x for xl in collected_x_val for xs in xl for x in xs]
        flat_y_train = [y for yl in collected_y_train for ys in yl for y in ys]
        flat_y_val = [y for yl in collected_y_val for ys in yl for y in ys]

        self.assertEqual(results_x_train, flat_x_train)
        self.assertEqual(results_x_val, flat_x_val)
        self.assertEqual(results_y_train, flat_y_train)
        self.assertEqual(results_y_val, flat_y_val)

    def test09_big_data(self):
        def define_rdf(num_of_entries):
            df = ROOT.RDataFrame(num_of_entries)\
                .Define("b1", "(int) rdfentry_")\
                .Define("b2", "(double) rdfentry_ * 2")\
                .Define("b3", "(int) rdfentry_ + 10192")\
                .Define("b4", "(int) -rdfentry_")\
                .Define("b5", "(double) -rdfentry_ - 10192")
            
            return df
        
        def test(size_of_batch, size_of_chunk, num_of_entries):
            gen_train, gen_validation = ROOT.TMVA.Experimental.CreateNumPyGenerators(
            batch_size=size_of_batch,
            chunk_size=size_of_chunk,
            rdataframe=define_rdf(num_of_entries),
            target=["b3","b5"],
            weights="b2",
            validation_split=0.3,
            shuffle=False,
            drop_remainder=False
            )

            collect_x = []
            n_train_batches, n_val_batches, train_remainder, val_remainder =\
                self.size_of_remainders(num_of_entries=num_of_entries, batch_size=size_of_batch, chunk_size=size_of_chunk)

            for _ in range(n_train_batches):
                x, y, z = next(gen_train)

                self.assertTrue(x.shape==(size_of_batch,2))
                self.assertTrue(y.shape==(size_of_batch,2))
                self.assertTrue(z.shape==(size_of_batch,1))

                self.assertTrue(np.all(x[:,0]*(-1)==x[:,1]))
                self.assertTrue(np.all(x[:,0]+10192==y[:,0]))
                # self.assertTrue(np.all(x[:,0]*(-1)-10192==y[:,1]))
                self.assertTrue(np.all(x[:,0]*2==z[:,0]))

                collect_x.extend(list(x[:,0]))
            
            if train_remainder:
                x, y, z = next(gen_train)
                self.assertTrue(x.shape==(train_remainder,2))
                self.assertTrue(y.shape==(train_remainder,2))
                self.assertTrue(z.shape==(train_remainder,1))

            for _ in range(n_val_batches):
                x, y, z = next(gen_validation)

                self.assertTrue(x.shape==(size_of_batch,2))
                self.assertTrue(y.shape==(size_of_batch,2))
                self.assertTrue(z.shape==(size_of_batch,1))

                self.assertTrue(np.all(x[:,0]*(-1)==x[:,1]))
                self.assertTrue(np.all(x[:,0]+10192==y[:,0]))
                # self.assertTrue(np.all(x[:,0]*(-1)-10192==y[:,1]))
                self.assertTrue(np.all(x[:,0]*2==z[:,0]))
                
                collect_x.extend(list(x[:,0]))
            
            if val_remainder:
                x, y, z = next(gen_validation)
                self.assertTrue(x.shape==(val_remainder,2))
                self.assertTrue(y.shape==(val_remainder,2))
                self.assertTrue(z.shape==(val_remainder,1))
            
            self.assertTrue(set(collect_x)==(i for i in range(num_of_entries)))
        
        test(400, 2000, 10100)


if __name__ == 'main':
    unittest.main()
