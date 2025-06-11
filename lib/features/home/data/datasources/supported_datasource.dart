import 'package:currency_converter_app/features/home/data/models/supported_currency_model.dart';
import 'package:currency_converter_app/features/home/domain/entity/supported_currency.dart';
import 'package:dio/dio.dart';

abstract class SupportedDatasource {
  Future<List<SupportedCurrency>> getSupportedCurrency();
}

class SupportedDatasourceImpl implements SupportedDatasource {
  final Dio dio;

  SupportedDatasourceImpl(this.dio);

  @override
  Future<List<SupportedCurrency>> getSupportedCurrency() async {
    final response = await dio.get('https://api');
    if (response.statusCode == 200) {
      final list =
          (response.data['items'] as List)
              .map((e) => SupportedCurrencyModel.fromMap(e))
              .toList();
      return list;
    } else {
      //Retornando para o repository, onde ele retornará o Either
      throw Exception();
    }
  }
}
